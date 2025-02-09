from telebot.types import BotCommand


default_commands = [
    BotCommand("reset", "Сбросить настройки"),
    BotCommand("change", "Изменить настройки"),
    BotCommand("help", "Помощь"),
    BotCommand("cancel", "Остановить бота"),
]