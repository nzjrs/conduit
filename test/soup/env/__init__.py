
import os, sys

from soup.utils.pluginloader import PluginLoader

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


class _EnvironmentLoader(PluginLoader):
    _subclass_ = EnvironmentWrapper
    _module_ = "soup.env"
    _path_ = os.path.dirname(__file__)

EnvironmentLoader = _EnvironmentLoader()
