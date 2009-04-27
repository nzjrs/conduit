
import os, sys
cwd = os.path.dirname(__file__)
root = os.path.abspath(os.path.join(cwd, '..', '..'))
sys.path.insert(0, root)

import unittest

import modules
import data

import conduit
import conduit.utils as Utils
import conduit.MappingDB as MappingDB
import conduit.Module as Module
import conduit.TypeConverter as TypeConverter
import conduit.Synchronization as Synchronization
import conduit.ModuleWrapper as ModuleWrapper

conduit.SHARED_MODULE_DIR = os.path.join(root,"conduit","modules")

print conduit.SHARED_MODULE_DIR

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
    def name(self):
        """ Returns the name of the class. We need to override this on generated classes """
        return self.__class__.__name__

    def shortDescription(self):
        """ Describe the test that is currently running
            Returns something like TestClass.test_function: Tests how good Conduit is """
        return "%s.%s: %s" % (self.name(), self.testMethodName, super(TestCase, self).shortDescription())

    def setUp(self):
        #Set up our own mapping DB so we dont pollute the global one
        dbFile = os.path.join(os.environ['TEST_DIRECTORY'],Utils.random_string()+".db")
        conduit.GLOBALS.mappingDB = MappingDB.MappingDB(dbFile)

        self.modules = Module.ModuleManager([conduit.SHARED_MODULE_DIR])
        conduit.GLOBALS.moduleManager = self.modules
        self.modules.load_all(whitelist=None, blacklist=None)

        self.type_converter = conduit.TypeConverter.TypeConverter(self.modules)
        conduit.GLOBALS.typeConverter = self.type_converter
        self.sync_manager = conduit.Synchronization.SyncManager(self.type_converter)
        conduit.GLOBALS.syncManager = self.sync_manager

    def tearDown(self):
        pass

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

    def is_online(self):
        try:
            return os.environ["CONDUIT_ONLINE"] == "TRUE"
        except KeyError:
            return False

    def is_interactive(self):
        try:
            return os.environ["CONDUIT_INTERACTIVE"] == "TRUE"
        except KeyError:
            return False

