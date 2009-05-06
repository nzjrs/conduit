
import os, sys
import unittest

def get_root():
    cwd = os.path.dirname(__file__)
    parts = cwd.split(os.path.sep)
    while len(parts) > 0:
        path = os.path.join(os.path.sep, *parts)
        if os.path.isfile(os.path.join(path, 'configure.ac')):
            return path
        parts.pop()
    raise NotImplementedError(get_root)

sys.path.insert(0, get_root())

import env
import data
import modules

import conduit
import conduit.utils as Utils
import conduit.MappingDB as MappingDB
import conduit.Module as Module
import conduit.TypeConverter as TypeConverter
import conduit.Synchronization as Synchronization
import conduit.ModuleWrapper as ModuleWrapper
import conduit.Conduit as Conduit
import conduit.Settings as Settings

conduit.IS_INSTALLED =              False
conduit.IS_DEVELOPMENT_VERSION =    True
conduit.SHARED_DATA_DIR =           os.path.join(get_root(),"data")
conduit.SHARED_MODULE_DIR =         os.path.join(get_root(),"conduit","modules")
conduit.FILE_IMPL =                 os.environ.get("CONDUIT_FILE_IMPL","GIO")
conduit.BROWSER_IMPL =              os.environ.get("CONDUIT_BROWSER_IMPL","system")
conduit.SETTINGS_IMPL =             os.environ.get("CONDUIT_SETTINGS_IMPL","GConf")
conduit.GLOBALS.settings =          Settings.Settings()

CHANGE_ADD = 1
CHANGE_REPLACE = 2
CHANGE_DELETE = 3


def get_module(name):
    """ This is just to avoid importing sys everywhere and i want my tests to be pretty! """
    return sys.modules[name]

class TestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(TestCase, self).__init__(methodName)
        self.testMethodName = methodName
        self.testMethod = getattr(self, methodName)

    @classmethod
    def name(cls):
        """ Returns the name of the class. We need to override this on generated classes """
        return cls.__name__

    def id(self):
        """ Returns the name of the class and the test this particular instance will run """
        return self.name() + "." + self.testMethodName

    def shortDescription(self):
        """ Describe the test that is currently running
            Returns something like TestClass.test_function: Tests how good Conduit is """
        return "%s.%s: %s" % (self.name(), self.testMethodName, super(TestCase, self).shortDescription())

    def setUpSync(self):
        #Set up our own mapping DB so we dont pollute the global one
        dbFile = os.path.join(os.environ['TEST_DIRECTORY'],Utils.random_string()+".db")
        conduit.GLOBALS.mappingDB = MappingDB.MappingDB(dbFile)

        self.modules = Module.ModuleManager([])
        conduit.GLOBALS.moduleManager = self.modules
        self.modules.load_all(whitelist=None, blacklist=None)

        self.type_converter = conduit.TypeConverter.TypeConverter(self.modules)
        conduit.GLOBALS.typeConverter = self.type_converter
        self.sync_manager = conduit.Synchronization.SyncManager(self.type_converter)
        conduit.GLOBALS.syncManager = self.sync_manager

    def get_dataprovider(self, name):
        wrapper = None
        for dp in self.modules.get_all_modules():
            if dp.classname == name:
                wrapper = self.modules.get_module_wrapper_with_instance(dp.get_key())
        assert wrapper != None
        return wrapper

    def get_dataprovider_factory(self, className, die=True):
        factory = None
        for f in self.model.dataproviderFactories:
            if f.__class__.__name__ == className:
                factory = f
        assert factory != None
        return factory

    def wrap_dataprovider(self, dp):
        wrapper = ModuleWrapper.ModuleWrapper(
                         klass=dp.__class__,
                         initargs=(),
                         category=None
                         )
        wrapper.module = dp
        return wrapper

    def networked_dataprovider(self, dp):
        """
        Dirty evil cludge so we can test networked sync...
        """
        factory = self.get_dataprovider_factory("NetworkServerFactory")
        server = factory.share_dataprovider(dp)
        assert server != None

        conduit = Conduit.Conduit(self.sync_manager)
        time.sleep(1)

        factory = self.get_dataprovider_factory("NetworkClientFactory")
        newdp = factory.dataprovider_create("http://localhost", conduit.uid, server.get_info())
        assert newdp != None
        return self.wrap_dataprovider( newdp() )

    def create_conduit(self):
        return Conduit.Conduit(self.sync_manager)

    def create_syncset(self):
        return SyncSet.SyncSet(
            moduleManager=self.modules,
            syncManager=self.sync_manager
        )


#
# Custom exceptions
#

class TestSkipped(Exception):
    """ Indicate a test was intentionally skipped rather than failed """


class UnavailableFeature(Exception):
    """ A feature required for this test was unavailable """


#
# 'Features'
# Some tests need things that might not be available, like python gpod, so provide an interface
# to fail gracefully.
#

class Feature(object):

    def __init__(self):
        self._cached = None

    def probe(self):
        raise NotImplementedError

    def available(self):
        if self._cached == None:
            self._cached = self.probe()
        return self._cached

    def require(self):
        if not self.available():
            raise UnavailableFeature

    @classmethod
    def name(cls):
        return cls.__name__

    def __str__(self):
        return self.name()


class _HumanInteractivity(Feature):

    def probe(self):
        try:
            return os.environ["CONDUIT_INTERACTIVE"] == "TRUE"
        except:
            return False

HumanInteractivity = _HumanInteractivity()


class _Online(Feature):

    def probe(self):
        try:
            return os.environ["CONDUIT_ONLINE"] == "TRUE"
        except:
            return False

Online = _Online()


#
# Custom test loader
#

class TestLoader(unittest.TestLoader):

    def __init__(self, include=None, exclude=None):
        self.include = include or []
        self.exclude = exclude or []

    def _flatten(self, tests):
        if isinstance(tests, unittest.TestSuite):
            for test in tests:
                for subtest in self._flatten(test):
                    yield subtest
        else:
            yield tests

    def loadTestsFromModule(self, module):
        for test in self._flatten(super(TestLoader, self).loadTestsFromModule(module)):
            if len(self.include) > 0:
                is_included = False
                for i in self.include:
                    if i in test.id():
                        is_included = True
                if not is_included:
                    continue
            if len(self.exclude) > 0:
                is_excluded = False
                for x in self.exclude:
                    if x in test.id():
                        is_excluded = True
                if is_excluded:
                    continue
            yield test

    def loadTestsFromMain(self):
        """ Load all tests that can be found starting from __main__ """
        return self.loadTestsFromModule(__import__('__main__'))

