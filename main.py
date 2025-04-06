import os
import time
import config
import telebot
import schedule
import requests
import threading

from datetime import datetime
from dotenv import load_dotenv
from telebot import TeleBot, types
from utils import logger, location as gps
from utils.commands import default_commands
from contents import output
from contents.emoji import emoji_dict


load_dotenv(override=True)
tg_api_token = os.getenv("TG_API_TOKEN")
weather_api_key = os.getenv("WEATHER_API_KEY")

bot = TeleBot(tg_api_token)
logger_dev = logger.setup_logger()


class WeatherBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.users = {}
        self.weather_api_key = weather_api_key
        self.setup_handlers()

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.users[message.chat.id] = {}
            self.bot.reply_to(message, "Привет! Я бот погоды. Давайте настроим ваши уведомления.")
            self.ask_city(message.chat.id)

        @self.bot.message_handler(commands=['reset'])
        def handle_reset(message):
            self.reset_user_data(message.chat.id)

        @self.bot.message_handler(commands=['now'])
        def get_weather_now(message: types.Message):
            chat_id = message.chat.id
            location = self.users.get(chat_id, {}).get("location")
            if not location:
                self.bot.send_message(chat_id, "❌ Локация не настроена. Используйте /start для настройки.")
                return
            self.send_weather(chat_id)

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            chat_id = message.chat.id
            if message.text == '/change':
                self.bot.send_message(chat_id, "Что вы хотите изменить? Выберите: location или time")
                self.users[chat_id]["state"] = "waiting_for_change"
            elif chat_id not in self.users:
                self.users[chat_id] = {"state": "waiting_for_location"}
                self.ask_location(chat_id)
            else:
                state = self.users[chat_id]["state"]
                if state == "waiting_for_location":
                    self.set_location(chat_id, message.text)
                elif state == "waiting_for_time":
                    self.set_time(chat_id, message.text)
                elif state == "waiting_for_change":
                    if message.text.lower() == "location":
                        self.ask_location(chat_id)
                    elif message.text.lower() == "time":
                        self.bot.send_message(chat_id, "Введите новое время для ежедневного уведомления (в формате ЧЧ:ММ):")
                        self.users[chat_id]["state"] = "waiting_for_time"
                    else:
                        self.bot.send_message(chat_id, "Пожалуйста, выберите 'location' или 'time'")

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_query(call):
            chat_id = call.message.chat.id

            if call.data == "Другой":
                self.ask_location(chat_id)  # Перенаправляем пользователя на ask_location()
            elif call.data in ["08:00", "12:00", "18:00"]:
                self.set_time(chat_id, call.data)  # Устанавливаем время уведомления
            else:
                self.set_location(chat_id, call.data)  # Устанавливаем местоположение

    def ask_city(self, chat_id):
        markup = types.InlineKeyboardMarkup(row_width=2)

        for city in config.cities.keys():
            button = types.InlineKeyboardButton(text=city, callback_data=city)
            markup.add(button)

        # Добавляем кнопку "Другой"
        other_button = types.InlineKeyboardButton(text="Другой", callback_data="Другой")
        markup.add(other_button)
        self.bot.send_message(chat_id, "Пожалуйста, выберите город:", reply_markup=markup)

    def ask_location(self, chat_id):
        if chat_id not in self.users:
            self.users[chat_id] = {}
        self.bot.send_message(chat_id, "Пожалуйста, введите название города:")
        self.users[chat_id] = {"state": "waiting_for_location"}

    def set_location(self, chat_id, location_name):
        try:
            data_city = gps.search_city(location_name)
            if data_city is None:
                error_message = "Город не найден."
                raise ValueError(error_message)
        except ValueError as e:
            logger_dev.error(e)
            self.bot.send_message(chat_id, "❌ Не удалось найти город. Пожалуйста, введите корректное название.")
            return

        try:
            lat, lon = float(data_city['lat']), float(data_city['lon'])
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url)
            response.raise_for_status()  # Это выбросит исключение для статусов 4xx и 5xx
            data = response.json()

            # Проверяем код ответа от API
            if data.get("cod") != 200:
                raise ValueError("Код ответа не равен 200")

        except (requests.exceptions.RequestException, ValueError):
            self.bot.send_message(chat_id, "❌ Не удалось найти город. Пожалуйста, введите корректное название.")
            return

        self.users[chat_id]["location"] = {
            "city": data_city['city'],
            "lat": lat,
            "lon": lon
        }
        self.users[chat_id]["state"] = "waiting_for_time"
        self.bot.send_message(chat_id, "Отлично! Теперь введите время для ежедневного уведомления (в формате ЧЧ:ММ):")

    def set_time(self, chat_id, time_str):
        try:
            datetime.strptime(time_str, "%H:%M")

            if chat_id not in self.users:
                return

            self.users[chat_id]["time"] = time_str
            self.users[chat_id]["state"] = "configured"
            self.bot.send_message(chat_id, f"Настройка завершена! Вы будете получать уведомления в {time_str} ежедневно.")
            self.schedule_weather(chat_id)
        except ValueError:
            self.bot.send_message(chat_id, "Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")

    def get_weather(self, location: tuple):
        city = location["city"]
        lat = location["lat"]
        lon = location["lon"]
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.weather_api_key}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()
        if data.get("cod") == 200:
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            description = data["weather"][0]["description"]
            icon_code = data["weather"][0]["icon"]

            weather_emoji = self.get_weather_emoji(icon_code)

            content = output.WEATHER_OUTPUT_FORMAT.format(
                city=city,
                weather_emoji=weather_emoji,
                description=description.capitalize(),
                temp=temp,
                feels_like=feels_like,
                humidity=humidity,
                wind_speed=wind_speed,
                visibility=data['visibility'] / 1000  # Переводим в километры
            )
            return content
        else:
            return "❌ Не удалось получить информацию о погоде."

    def get_weather_emoji(self, icon_code):
        return emoji_dict.get(icon_code, "🌈")

    def send_weather(self, chat_id):
        try:
            location = self.users.get(chat_id, {}).get("location")
            if not location:
                self.bot.send_message(chat_id, "❌ Локация не настроена. Используйте /start для настройки.")
                return
            weather_info = self.get_weather(location)
            current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
            message = f"⏰ Время: {current_time}\n\n{weather_info}"
            self.bot.send_message(chat_id, message)
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            self.bot.send_message(chat_id, "❌ Произошла ошибка. Попробуйте позже.")

    def reset_user_data(self, chat_id):
        if chat_id in self.users:
            del self.users[chat_id]
        self.bot.send_message(chat_id, "Настройки сброшены.")
        self.ask_location(chat_id)

    def schedule_weather(self, chat_id):
        if chat_id in self.users and "job" in self.users[chat_id]:
            schedule.cancel_job(self.users[chat_id]["job"])
        job = schedule.every().day.at(self.users[chat_id]["time"]).do(self.send_weather, chat_id)
        self.users[chat_id]["job"] = job

    def run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def run(self):
        schedule_thread = threading.Thread(target=self.run_schedule)
        schedule_thread.start()
        self.bot.set_my_commands(default_commands)
        self.bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    bot = WeatherBot(tg_api_token)
    logger_dev.debug("Start app")
    bot.run()
