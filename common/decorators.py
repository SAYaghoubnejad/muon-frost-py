import time
from typing import List
import requests
import logging
from web3 import Web3
from common.utils import Utils


def seed_validation_decorator(handler):
    def wrapper(list: List, seed: int, subset_size: int):
        if validate_seed(int(time.time()), seed):
            return handler(list, seed, subset_size)
        else:
            raise Exception("Unauthorized random seed.") 
    return wrapper

#Interface
def validate_seed(seed: int) -> bool:
    #validate your seed here for random subnet selection:
    last_block_hash = Utils.get_last_block_hash()
    if not last_block_hash:
        return False
    
    hash = Web3.solidity_keccak (
                ['string'],
                [last_block_hash]
                # Add more parameters to validate seed...
            )

    int_hash = int.from_bytes(hash, 'big')
    
    return seed == int_hash


def get_valid_random_seed(retry: int = 3) -> int:
    last_block_hash = Utils.get_last_block_hash()
    while not last_block_hash:
        last_block_hash = Utils.get_last_block_hash()
        retry += 1
        if retry == 3:
            return None
    
    hash = Web3.solidity_keccak (
                ['string'],
                [last_block_hash]
                # Add more parameters to get a verified seed...
            )

    int_hash = int.from_bytes(hash, 'big')

    return int_hash




    

