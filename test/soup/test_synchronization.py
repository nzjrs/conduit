
import soup
from soup.modules import ModuleLoader

import conduit

#FIXME: Work out which of these i can drop :)
import os
import conduit
import conduit.utils as Utils
import conduit.MappingDB as MappingDB
import conduit.Module as Module
import conduit.TypeConverter as TypeConverter
import conduit.Synchronization as Synchronization
import conduit.ModuleWrapper as ModuleWrapper
import conduit.Conduit as Conduit
import conduit.Settings as Settings

def make_testcase(src, src_data, snk, snk_data):
    class TestSynchronization(soup.utils.test.TestCase):
        source_class = src
        source_data_class = src_data
        sink_class = snk
        sink_data_class = snk_data

        @classmethod
        def name(self):
            return "TestSynchronization%s%s" % (self.source_class.name(), self.sink_class.name())

        def requires(self):
            for obj in (self.source_class, self.source_data_class, self.sink_class, self.sink_data_class):
                for thing in obj.requires:
                    yield thing

        def setUpSync(self):
            # FIXME: I'd put this in an EnvironmentWrapper, but i need priorities before i can do that :/
            conduit.IS_INSTALLED =              False
            conduit.IS_DEVELOPMENT_VERSION =    True
            conduit.SHARED_DATA_DIR =           os.path.join(soup.get_root(),"data")
            conduit.SHARED_MODULE_DIR =         os.path.join(soup.get_root(),"conduit","modules")
            conduit.BROWSER_IMPL =              os.environ.get("CONDUIT_BROWSER_IMPL","system")
            conduit.SETTINGS_IMPL =             os.environ.get("CONDUIT_SETTINGS_IMPL","Python")
            conduit.GLOBALS.settings =          Settings.Settings()

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


        def setUp(self):
            super(TestSynchronization, self).setUp()
            self.setUpSync()

            self.source = self.source_class(self)
            self.source_data = self.source_data_class()
            self.sink = self.sink_class(self)
            self.sink_data = self.sink_data_class()

            self.pair = self.create_conduit()
            self.pair.add_dataprovider(self.source.get_wrapped())
            self.pair.add_dataprovider(self.sink.get_wrapped())

            self.pair.enable_two_way_sync()
            self.pair.set_policy("conflict", "replace")
            self.pair.set_policy("deleted", "replace")

        def tearDown(self):
            # we always do a no changes sync at the end, and make sure there are no changes...
            self.pair.sync(block=True)
            self.source.destroy_dataprovider()
            self.sink.destroy_dataprovider()

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


        def add_testdata(self, target, target_data):
            count = 0
            for data in target_data.iter_samples():
                count += 1
                target.add(data)
            return count

        def modify_testdata(self, target, target_data):
            uids = target.get_all()
            for uid in uids:
                data = target_data.mutate_sample(target.get(uid))
                target.replace(uid, data)

        def check_state(self, expected):
            source_count, sink_count = self.source.get_num_items(), self.sink.get_num_items()
            assert source_count == sink_count, "source has %d, sink has %d, expected %d" % (source_count, sink_count, expected)
            assert source_count == expected, "dataproviders have %d, expected %d" % (source_count, expected)

        def test_empty_sync(self):
            """ test empty synchronisation """
            self.pair.sync(block=True)

        def test_add_to_source(self):
            """ should be able to add data to source then sync """
            added = self.add_testdata(self.source, self.source_data)
            self.pair.sync(block=True)
            self.check_state(added)
            return added

        def test_add_source_modify_source(self):
            """ should be able to add data to source, sync, modify source, then sync """
            added = self.test_add_to_source()
            self.modify_testdata(self.source, self.source_data)
            self.pair.sync(block=True)
            self.check_state(added)

        def test_add_source_modify_sink(self):
            """ should be able to add data to source, sync, modify sink, then sync """
            added = self.test_add_to_source()
            self.modify_testdata(self.sink, self.sink_data)
            self.pair.sync(block=True)
            self.check_state(added)

        def test_add_source_delete_source(self):
            """ should be able to add data at source, sync, delete data from source then sync """
            self.test_add_to_source()
            self.source.delete_all()
            self.pair.sync(block=True)
            self.check_state(0)

        def test_add_source_delete_sink(self):
            """ should be able to add data at source, sync, delete at sink, then sync """
            self.test_add_to_source()
            self.sink.delete_all()
            self.pair.sync(block=True)
            self.check_state(0)

        def test_add_to_sink(self):
            """ should be able to add data to sink then sync """
            added = self.add_testdata(self.sink, self.sink_data)
            self.pair.sync(block=True)
            self.check_state(added)
            return added

        def test_add_sink_modify_source(self):
            """ should be able to add data to sink, sync, modify source, then sync """
            added = self.test_add_to_sink()
            self.modify_testdata(self.source, self.source_data)
            self.pair.sync(block=True)
            self.check_state(added)

        def test_add_sink_modify_sink(self):
            """ should be able to add data to sink, sync, modify sink, then sync """
            added = self.test_add_to_sink()
            self.modify_testdata(self.sink, self.sink_data)
            self.pair.sync(block=True)
            self.check_state(added)

        def test_add_sink_delete_source(self):
            """ should be able to add data at sink, sync, delete at source, then sync """
            self.test_add_to_sink()
            self.source.delete_all()
            self.pair.sync(block=True)
            self.check_state(0)

        def test_add_sink_delete_sink(self):
            """ should be able to add data at sink, sync, delete at sink, then sync """
            self.test_add_to_sink()
            self.sink.delete_all()
            self.pair.sync(block=True)
            self.check_state(0)

    return TestSynchronization


# Generate all the variations of TestSynchronization
self = soup.get_module(__name__)
mods = ModuleLoader.get_all()
for i in range(len(mods)):
    for j in range(len(mods)):
        source = mods[i]
        sink = mods[j]

        # Cludge: If we have 2 different datatypes, we implicity use a wrapper
        # that converts from the most specialized to the lease specialized datatype.
        # That way we have Contact files instead of Mp3 files etc.
        if source.dataclass == sink.dataclass:
            source_data = source.dataclass
            sink_data = sink.dataclass
        #elif source.dataclass.is_compatible(sink.dataclass.get_datatype():
        #    source_data = source.dataclass
        #    sink_data = # conversion thingy here
        #elif sink.dataclass.is_compatible(source.dataclass.get_datatype()):
        #    source_data = # conversion thingy here
        #    sink_data = sink.dataclass
        else:
            continue

        # Right now we only test twoway sync. We should seperate the twoway specific tests out.
        # We should also test slow-sync *shrug*
        if not source.is_twoway() or not sink.is_twoway():
            continue

        # Actually generate a testcase for this..
        testklass = make_testcase(source, source_data, sink, sink_data)
        setattr(self, testklass.name(), testklass)


# Allow people to run the test directly
if __name__ == "__main__":
    import unittest
    unittest.main()
