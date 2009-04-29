import soup

def make_testcase(src, snk):
    class TestSynchronization(soup.TestCase):
        source_klass = src
        sink_klass = snk

        @classmethod
        def name(self):
            return "TestSynchronization%s%s" % (self.source_klass.name(), self.sink_klass.name())

        def setUp(self):
            self.setUpSync()

            self.source = self.source_klass(self)
            self.sink = self.sink_klass(self)
            self.pair = self.create_conduit()

        def testDoNothing(self):
            """ Test doing nothing """
            pass

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
        testklass = make_testcase(source, sink)
        setattr(self, testklass.name(), testklass)


# Allow people to run the test directly
if __name__ == "__main__":
    import unittest
    unittest.main()
