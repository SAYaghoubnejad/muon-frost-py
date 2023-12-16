from typing import List
from frost_mpc.abstract.data_manager import DataManager

import json
import time

class NodeDataManager(DataManager):
    def __init__(self) -> None:
        super().__init__()
        self.__dkg_keys = {}
        self.__nonces = []
    
    def set_nonces(self, nonces_list: List) -> None:
        self.__nonces = nonces_list
    
    def get_nonces(self):
        return self.__nonces
    
    def set_dkg_key(self, key, value) -> None:
        self.__dkg_keys[key] = value
        
    def get_dkg_key(self, key):
        return self.__dkg_keys.get(key, {})
    

