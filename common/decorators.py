import time
from typing import List
import requests
import logging
from web3 import Web3



def seed_validation_decorator(handler):
    def wrapper(list: List, seed: int, subset_size: int):
        if validate_seed(int(time.time()), seed):
            return handler(list, seed, subset_size)
        else:
            raise Exception("Unauthorized random seed.") 
    return wrapper


def validate_seed(timestamp, seed) -> bool:
    last_block_hash = get_last_block_hash()
    if not last_block_hash:
        return False
    
    hash = Web3.solidity_keccak (
                ['uint256', 'string'],
                [timestamp,  last_block_hash]
            )

    int_hash = int.from_bytes(hash, 'big')
    
    return seed == int_hash






def get_last_block_hash() -> str:
    blockchain_url = "https://blockchain.info/latestblock"
    try:
        response = requests.get(blockchain_url)
        if response.status_code == 200:
            latest_block_data = response.json()
            last_block_hash = latest_block_data["hash"]
            return last_block_hash
        else:
            logging.error(f"Error: Unable to fetch the latest block (status code {response.status_code})")
            return None
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        return None

def get_valid_random_seed(retry: int = 3) -> int:
    last_block_hash = get_last_block_hash()
    while not last_block_hash:
        last_block_hash = get_last_block_hash()
        retry += 1
        if retry == 3:
            return None
    
    hash = Web3.solidity_keccak (
                ['uint256', 'string'],
                [int(time.time()),  last_block_hash]
            )

    int_hash = int.from_bytes(hash, 'big')

    return int_hash




    

