import logging
import logging.handlers
import os

class LoggerSingleton:
    _instance = None

    @classmethod
    def get_instance(cls, env='development'):
        """
        Получает единственный экземпляр логгера.

        :param env: Строка, указывающая среду ('development' или 'production').
        :return: Настроенный экземпляр логгера.
        """
        if cls._instance is None:
            cls._instance = cls._setup_logger(env)
        return cls._instance

    @classmethod
    def _setup_logger(cls, env):
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
        elif env == 'production':
            log_level = logging.INFO
            log_file = os.path.join(log_dir, 'bot.log')
        else:
            raise ValueError("Неверная среда. Используйте 'development' или 'production'.")

        # Создаем экземпляр логгера
        logger = logging.getLogger('TelegramBotLogger')
        
        # Устанавливаем уровень логирования
        logger.setLevel(log_level)

        # Проверяем, есть ли уже обработчики у логгера (чтобы избежать дублирования)
        if not logger.handlers:
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

        return logger

# Пример использования:
if __name__ == "__main__":
    logger = LoggerSingleton()
    logger_dev = logger.get_instance(env='development')  # Получаем единственный экземпляр для разработки
    
    logger_dev.debug("Это отладочное сообщение.")
    
    logger_prod = LoggerSingleton.get_instance(env='production')  # Получаем единственный экземпляр для продакшена
    
    logger_prod.info("Это информационное сообщение.")