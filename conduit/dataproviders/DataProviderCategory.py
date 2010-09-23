class DataProviderCategory:
    CATEGORIES = {}
    def __init__(self, name, icon="image-missing", key=""):
        if name not in DataProviderCategory.CATEGORIES:
            DataProviderCategory.CATEGORIES[name] = self
        self.name = name
        self.icon = icon
        self.key = name + key
