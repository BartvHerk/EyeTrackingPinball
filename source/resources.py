import numpy as np
from IO import import_fields, load_settings, save_settings, import_references, import_recordings


class Resources:
    _instance = None


    def __new__(cls, *args, **kwargs): # Singleton
        if cls._instance is None:
            cls._instance = super(Resources, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance


    def __init__(self):
        if not self.__initialized:
            self.__initialized = True
            self._H_inv_field = None

            # Import resources
            self.settings = load_settings()
            self.references = import_references()
            self.fields = import_fields()
            self.recordings = import_recordings()
    

    def save_settings_changes(self):
        save_settings(self.settings)
    

    def recalculate_exports(self):
        for recording in self.recordings:
            recording._export = None