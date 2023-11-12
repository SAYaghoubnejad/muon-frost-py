import importlib
import logging
import uuid


class Utils:
    def __init__(self) -> None:
        pass

    @staticmethod
    def call_external_method(script_file, method_name, *args, **kwargs):
        try:
            module = importlib.import_module(script_file)
            class_name = getattr(module, 'CLASS_NAME')
            cls = getattr(module, class_name)
            method_to_call = getattr(cls, method_name)
            return method_to_call(*args, **kwargs)
        except ModuleNotFoundError:
            logging.error(f"Error: {script_file} not found", exc_info=True)
            return None
        except AttributeError:
            logging.error(
                f"Error: {method_name} not found in {script_file}", exc_info=True)
            return None
        except Exception as e:
            logging.error(f"Unhandled error: ", exc_info=True)
            return None
        
    @staticmethod
    def generate_random_uuid() -> str:
        """
        Generates a random UUID.

        Returns:
        str: A randomly generated UUID.
        """
        return str(uuid.uuid4())
    
    # TODO: add rotation
