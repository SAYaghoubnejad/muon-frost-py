
import logging
import os


class ConfigurationSettings:
    def __init__(self) -> None:
        pass


    @staticmethod
    def set_logging_options(file_path: str, file_name: str) -> None:
        log_formatter = logging.Formatter('%(asctime)s - %(message)s', )
        root_logger = logging.getLogger()
        
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        
        with open(f'{file_path}/{file_name}', "w"):
            pass

        file_handler = logging.FileHandler(f'{file_path}/{file_name}')
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.INFO)
    