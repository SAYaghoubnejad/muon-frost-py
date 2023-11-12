import importlib
import logging



class Utils:
    def __init__(self) -> None:
        pass


    @staticmethod
    def call_external_method(script_file, method_name, *args, **kwargs):
        try:
            script_module = importlib.import_module(script_file)
            method_to_call = getattr(script_module, method_name)
            return method_to_call(*args, **kwargs)
        except ModuleNotFoundError:
            logging.error(f"Error: {script_file} not found", exc_info=True)
            return None
        except AttributeError: 
            logging.error(f"Error: {method_name} not found in {script_file}", exc_info=True)
            return None
        except Exception as e:
            logging.error(f"Unhandled error: ", exc_info=True)
            return None
