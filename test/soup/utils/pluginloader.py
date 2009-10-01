
import sys
import os

class PluginLoader(object):
    """ Walks a directory and loads all modules within, providing access to anything that
        implements self._subclass_ """

    _subclass_ = None
    _module_ = None
    _path_ = None

    def load_modules(self):
        for root, dirs, files in os.walk(self._path_):
            for dir in dirs:
                if dir[:1] != ".":
                    self.load_module(dir)
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    self.load_module(file[:-3])
            break

    def load_module(self, module):
        if sys.modules.has_key(module):
            reload(sys.modules[module])
        else:
            __import__(self._module_, {}, {}, [module])

    def get_all(self):
        if len(self._subclass_.__subclasses__()) == 0:
            self.load_modules()
        return self._subclass_.__subclasses__()


