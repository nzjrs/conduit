import os, sys, glob

class DataWrapper(object):
    """
    This class provides a wrapper around some test data.
    """

    @classmethod
    def name(cls):
        return cls.__name__

    def get_data_dir(self):
        return os.path.join(os.path.dirname(__file__),"..","..","python-tests","data")

    def get_files_from_data_dir(self, glob_str):
        """ Yields files that match the glob in the data dir """
        files = []
        for i in glob.glob(os.path.join(self.get_data_dir(),glob_str)):
            yield os.path.abspath(i)

    def iter_samples(self):
        """ Yield DataType objects containing sample data """
        raise NotImplementedError

    def generate_sample(self):
        """ Generate a single DataType object with random data """
        raise NotImplementedError

    def mutate_sample(self, obj):
        """ Modify a DataType object randomly """
        raise NotImplementedError

def load_modules():
    basepath = os.path.dirname(__file__)
    for root, dirs, files in os.walk(basepath):
        for dir in dirs:
            if dir[:1] != ".":
                load_module(dir)
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                load_module(file[:-3])
        break

def load_module(module):
    if sys.modules.has_key(module):
        reload(sys.modules[module])
    else:
        __import__("soup.data", {}, {}, [module])

def get_all():
    if len(DataWrapper.__subclasses__()) == 0:
        load_modules()
    return DataWrapper.__subclasses__()

