import logging

class SingletonLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonLogger, cls).__new__(cls)
            cls._instance.logger = logging.getLogger('DocuSecureLogger')
            cls._instance.logger.setLevel(logging.INFO)
            handler = logging.FileHandler('logs/app.log')
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            handler.setFormatter(formatter)
            cls._instance.logger.addHandler(handler)
        return cls._instance

    def get_logger(self):
        return self.logger
