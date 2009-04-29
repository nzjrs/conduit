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

        def test_empty_sync(self):
            """ test empty synchronisation """
            self.pair.sync(block=True)

        def test_add_to_source(self):
            """ testing adding data to source """
            for data in self.data.iter_samples():
                self.source.add(data)
            self.pair.sync(block=True)

        def test_add_to_sink(self):
            """ test adding data to sink """
            for data in self.data.iter_samples():
                self.sink.add(data)
            self.pair.sync(block=True)

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
        testklass = make_testcase(source, sink, sink.dataclass)
        setattr(self, testklass.name(), testklass)


# Allow people to run the test directly
if __name__ == "__main__":
    import unittest
    unittest.main()
