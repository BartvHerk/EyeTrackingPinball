from IO import import_specifications, import_references, import_recordings


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

            # Import resources
            self.specifications = import_specifications()
            self.field_dimensions = float(self.specifications['field']['width']), float(self.specifications['field']['height'])
            self.references = import_references()
            self.recordings = import_recordings()