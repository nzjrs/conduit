import soup

def make_testcase(src, snk):
    class TestSynchronization(soup.TestCase):
        source = src
        sink = snk

        @classmethod
        def name(self):
            return "TestSynchronization%s%s" % (self.source.name(), self.sink.name())

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
        testklass = make_testcase(source, sink)
        setattr(self, testklass.name(), testklass)


# Allow people to run the test directly
if __name__ == "__main__":
    import unittest
    unittest.main()
