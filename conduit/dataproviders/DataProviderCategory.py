class DataProviderCategory:
    def __init__(self, name, icon="image-missing", key=""):
        self.name = name
        self.icon = icon
        if not key:
            key = name
        self.key = key
        
