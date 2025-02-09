import logging
import logging.handlers
import os
from .singleton import singleton


@singleton
def setup_logger(env='development'):
    """
    Настраивает логгер для Telegram-бота.

    :param env: Строка, указывающая среду ('development' или 'production').
    :return: Настроенный экземпляр логгера.
    """
    
    # Создаем директорию для хранения логов, если она не существует
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Определяем уровень логирования в зависимости от среды
    if env == 'development':
        log_level = logging.DEBUG
        log_file = os.path.join(log_dir, 'bot_debug.log')
        
        # Создаем обработчик для вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)  # Уровень вывода в консоль
        
        # Устанавливаем форматирование сообщений лога для консоли
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
    elif env == 'production':
        log_level = logging.INFO
        log_file = os.path.join(log_dir, 'bot.log')
        
        console_handler = None
    else:
        raise ValueError("Неверная среда. Используйте 'development' или 'production'.")

    # Создаем экземпляр логгера
    logger = logging.getLogger('TelegramBotLogger')
    
    # Устанавливаем уровень логирования
    logger.setLevel(log_level)

    # Создаем обработчик для записи логов в файл с ротацией
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # Максимальный размер файла лога (5 МБ)
        backupCount=5               # Количество резервных копий файлов лога
    )
    
    # Устанавливаем форматирование сообщений лога
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handler.setFormatter(formatter)
    
    # Добавляем обработчик к логгеру
    logger.addHandler(handler)
    
    if console_handler:
            logger.addHandler(console_handler)

    return logger

# Пример использования:
if __name__ == "__main__":
    logger = setup_logger(env='development')  # или env='production'
    
    logger.debug("Это отладочное сообщение.")
    logger.info("Это информационное сообщение.")