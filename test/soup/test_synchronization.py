import soup

def make_testcase(src, snk, dcls):
    class TestSynchronization(soup.TestCase):
        source_klass = src
        sink_klass = snk
        dataclass = dcls

        @classmethod
        def name(self):
            return "TestSynchronization%s%s" % (self.source_klass.name(), self.sink_klass.name())

        def setUp(self):
            self.setUpSync()

            self.data = self.dataclass()

            self.source = self.source_klass(self)
            self.sink = self.sink_klass(self)

            self.pair = self.create_conduit()
            self.pair.add_dataprovider(self.source.get_wrapped())
            self.pair.add_dataprovider(self.sink.get_wrapped())

            self.pair.enable_two_way_sync()
            self.pair.set_policy("conflict", "replace")
            self.pair.set_policy("deleted", "replace")

        def add_testdata(self, target):
            count = 0
            for data in self.data.iter_samples():
                count += 1
                target.add(data)
            return count

        def modify_testdata(self, target):
            uids = target.get_all()
            for uid in uids:
                data = self.data.mutate_sample(target.get(uid))
                target.replace(uid, data)

        def check_state(self, expected):
            source_count, sink_count = self.source.get_num_items(), self.sink.get_num_items()
            assert source_count == sink_count, "source has %d, sink has %d, expected %d" % (source_count, sink_count, expected)
            assert source_count == expected

        def tearDown(self):
            # we always do a no changes sync at the end, and make sure there are no changes...
            self.pair.sync(block=True)

        def test_empty_sync(self):
            """ test empty synchronisation """
            self.pair.sync(block=True)

        def test_add_to_source(self):
            """ should be able to add data to source then sync """
            added = self.add_testdata(self.source)
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
            added = self.add_testdata(self.sink)
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
mods = soup.modules.get_all()
for i in range(len(mods)):
    for j in range(i+1, len(mods)):
        source = mods[i]
        sink = mods[j]
        if sink.dataclass != source.dataclass:
            # FIXME: Need a generic way to say, hey you can sync contacts to folders
            continue
        if not source.is_twoway() or not sink.is_twoway():
            continue
        testklass = make_testcase(source, sink, sink.dataclass)
        setattr(self, testklass.name(), testklass)


# Allow people to run the test directly
if __name__ == "__main__":
    import unittest
    unittest.main()
