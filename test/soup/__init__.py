
import unittest

CHANGE_ADD = 1
CHANGE_REPLACE = 2
CHANGE_DELETE = 3

class BaseTest(unittest.TestCase):

    def grumpy(self):
        #Set up our own mapping DB so we dont pollute the global one
        dbFile = os.path.join(os.environ['TEST_DIRECTORY'],Utils.random_string()+".db")
        conduit.GLOBALS.mappingDB = MappingDB.MappingDB(dbFile)

        self.modules = Module.ModuleManager(dirs)
        conduit.GLOBALS.moduleManager = self.modules
        self.modules.load_all(whitelist=None, blacklist=None)

        self.type_converter = TypeConverter.TypeConverter(self.modules)
        conduit.GLOBALS.typeConverter = self.type_converter
        self.sync_manager = Synchronization.SyncManager(self.type_converter)
        conduit.GLOBALS.syncManager = self.sync_manager

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def get_dataprovider(self, key):
        wrapper = None
        for dp in self.model.get_all_modules():
            if dp.classname == name:
                wrapper = self.model.get_module_wrapper_with_instance(dp.get_key())
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

