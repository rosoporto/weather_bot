from telebot.types import BotCommand


default_commands = [
    BotCommand("now", "Прогноз погоды"),
    BotCommand("change", "Изменить настройки"),
    BotCommand("reset", "Сбросить настройки"),    
    BotCommand("help", "Помощь"),
    BotCommand("cancel", "Остановить бота"),
]