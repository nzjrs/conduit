import soup

def make_testcase(src, snk):
    class TestSynchronization(soup.TestCase):
        source = src
        sink = snk

        def testDoNothing(self):
            pass

    return TestSynchronization


self = soup.get_module(__name__)
mods = soup.modules.get_all()
for i in range(len(mods)):
    for j in range(i+1, len(mods)):
        source = mods[i]
        sink = mods[j]
        setattr(self, "TestSynchronization%s%s" % (source.name(), sink.name()), make_testcase(source, sink))


if __name__ == "__main__":
    import unittest
    unittest.main()
