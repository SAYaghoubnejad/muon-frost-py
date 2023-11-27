from typing import List
import logging


def seed_validation_decorator(handler):
    def wrapper(self, threshold: int, n: int, all_nodes: List[str], app_name: str, seed: int):
        if self.seed_validator(seed):
            return handler(threshold, n, all_nodes, app_name, seed)
        else:
            logging.error('Gateway Decorator => Exception occurred. Unauthorized random seed.')
            raise Exception("Unauthorized random seed.") 
    return wrapper
