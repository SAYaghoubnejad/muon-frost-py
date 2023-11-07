class DataManager:
    def __init__(self) -> None:
        self.__storage = {}

    def setup_database(self, database_name: str):
        self.__storage[database_name] = {}

    # Interface
    def save_data(self, database_name: str, key, value):
        self.__storage[database_name][key] = value

    # Interface
    def add_data(self, database_name: str, key, value):
        try:
            self.__storage[database_name][key].append(value)
        except:
            self.__storage[database_name][key] = [value]

    # Interface
    def remove_data(self, database_name: str, key, value):
        self.__storage[database_name][key].remove(value)

    # Interface
    def get_data(self, database_name: str, key):
        return self.__storage[database_name][key]