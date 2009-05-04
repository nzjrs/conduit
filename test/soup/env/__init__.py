
import os, sys

class EnvironmentWrapper(object):

    @classmethod
    def enabled(cls, opts):
        return True

    def prepare_environment(self):
        """ Modify the environment that the tests are running in """
        pass

    def decorate_test(self, test):
        """ Decorate a callable so that it can be run in the modified environment """
        return test

    def finalize_environment(self):
        """ Clean up the environment. Called at the very end of the test suite. """
        pass


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
        __import__("soup.env", {}, {}, [module])

def get_all():
    if len(EnvironmentWrapper.__subclasses__()) == 0:
        load_modules()
    return EnvironmentWrapper.__subclasses__()

