import os, sys

class DataWrapper(object):
    """
    This class provides a wrapper around some test data.
    """

    def get_all(self):
        raise NotImplementedError


def load_all_data():
    basepath = os.path.dirname(__file__)
    for root, dirs, files in os.walk(basepath):
        for dir in dirs:
            if dir[:1] != ".":
                load_data(dir)
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                load_data(file[:-3])
        break

def load_data(dw):
    if sys.modules.has_key(dw):
        reload(sys.modules[dw])
    else:
        __import__("soup.data", {}, {}, [dw])

def get_all():
    if len(DataWrapper.__subclasses__()) == 0:
        load_all_data()
    return DataWrapper.__subclasses__()

