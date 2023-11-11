class DataManager:
    """
    A class to manage in-memory data storage, organized in a dictionary format.
    The data is stored in the form of nested dictionaries, where each top-level
    dictionary represents a separate database.
    
    Note: If one wishes to use other data structures or another form of data, one 
    can inherit from this class and use the modified class. 
    """

    def __init__(self) -> None:
        """
        Initializes the DataManager with an empty storage structure.
        """
        self._storage = {}

    def setup_database(self, database_name: str) -> None:
        """
        Initializes a new database within the storage.

        Parameters:
        database_name (str): The name of the new database to be added.
        """
        self._storage[database_name] = {}

    def save_data(self, database_name: str, key, value) -> None:
        """
        Saves a single value under a specific key in the specified database.

        Parameters:
        database_name (str): The name of the database.
        key: The key under which the value is to be stored.
        value: The value to be stored.
        """
        self._storage[database_name][key] = value

    def add_data(self, database_name: str, key, value) -> None:
        """
        Adds a value to a list under a specific key in the specified database.
        If the key does not exist, it creates a new list.

        Parameters:
        database_name (str): The name of the database.
        key: The key under which the value is to be added.
        value: The value to be added.
        """
        if key not in self._storage[database_name].keys():
            self._storage[database_name][key] = []
        self._storage[database_name][key].append(value)

    def remove_data(self, database_name: str, key, value) -> None:
        """
        Removes a value from a list under a specific key in the specified database.

        Parameters:
        database_name (str): The name of the database.
        key: The key from which the value is to be removed.
        value: The value to be removed.
        """
        if value in self._storage[database_name][key]:
            self._storage[database_name][key].remove(value)

    def get_data(self, database_name: str, key):
        """
        Retrieves data stored under a specific key in the specified database.

        Parameters:
        database_name (str): The name of the database.
        key: The key for which data is to be retrieved.

        Returns:
        The data stored under the specified key in the specified database.
        """
        return self._storage[database_name].get(key, None)
