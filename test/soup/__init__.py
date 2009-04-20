
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

conduit.SHARED_MODULE_DIR = os.path.join(root,"conduit","modules")

CHANGE_ADD = 1
CHANGE_REPLACE = 2
CHANGE_DELETE = 3

def get_module(name):
    """ This is just to avoid importing sys everywhere and i want my tests to be pretty! """
    return sys.modules[name]

class TestCase(unittest.TestCase):

    def setUp(self):
        #Set up our own mapping DB so we dont pollute the global one
        dbFile = os.path.join(os.environ['TEST_DIRECTORY'],Utils.random_string()+".db")
        conduit.GLOBALS.mappingDB = MappingDB.MappingDB(dbFile)

        self.modules = Module.ModuleManager([root])
        conduit.GLOBALS.moduleManager = self.modules
        self.modules.load_all(whitelist=None, blacklist=None)

        self.type_converter = conduit.TypeConverter.TypeConverter(self.modules)
        conduit.GLOBALS.typeConverter = self.type_converter
        self.sync_manager = conduit.Synchronization.SyncManager(self.type_converter)
        conduit.GLOBALS.syncManager = self.sync_manager

    def tearDown(self):
        pass

    def get_dataprovider(self, key):
        wrapper = None
        for dp in self.modules.get_all_modules():
            if dp.classname == name:
                wrapper = self.modules.get_module_wrapper_with_instance(dp.get_key())
        assert wrapper != None
        return wrapper

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

