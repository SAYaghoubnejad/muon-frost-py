import importlib
import logging
import uuid
import random
from typing import List


class Utils:
    def __init__(self) -> None:
        pass

    @staticmethod
    def call_external_method(script_file: str, method_name: str, *args, **kwargs) -> None:
        try:
            module = importlib.import_module(script_file)
            class_name = getattr(module, 'CLASS_NAME')
            cls = getattr(module, class_name)
            method_to_call = getattr(cls, method_name)
            return method_to_call(*args, **kwargs)
        except ModuleNotFoundError:
            logging.error(f"Error: {script_file} not found")
            return None
        except AttributeError:
            logging.error(
                f"Error: {method_name} not found in {script_file}")
            return None
        except Exception as e:
            logging.error(f"Unhandled error: ")
            return None
        
    @staticmethod
    def generate_random_uuid() -> str:
        """
        Generates a random UUID.

        Returns:
        str: A randomly generated UUID.
        """
        return str(uuid.uuid4())
    
    # TODO: add a decorator to verify random seed
    @staticmethod
    def get_new_random_subset(list: List, seed: int, subset_size: int) -> None:
        random.seed(seed)  
        random_subset = random.sample(list, subset_size)
        return random_subset


