import soup

import pickle

def make_testcase(wrp):
    class TestDatatype(soup.TestCase):
        wrapperclass = wrp

        @classmethod
        def name(self):
            return "TestDatatype%s" % self.wrapperclass.name()

        def setUp(self):
            super(TestDatatype, self).setUp()
            self.wrapper = self.wrapperclass()

        def test_uid(self):
            """ Datatype should implemenent get_UID """
            obj = self.wrapper.iter_samples().next()
            assert obj.get_UID != None

        def test_rid(self):
            """ Datatype should implement get_rid """
            obj = self.wrapper.iter_samples().next()
            assert obj.get_rid() != None

        def test_pickle(self):
            """ Should be able to pickle a Datatype """
            obj = self.wrapper.iter_samples().next()
            pickled = pickle.dumps(obj)
            clone = pickle.loads(pickled)

            assert type(obj) == type(clone)
            assert obj.get_UID() == clone.get_UID()
            assert obj.get_mtime() == clone.get_mtime()
            assert obj.get_hash() == clone.get_hash()
            assert obj.get_rid() == clone.get_rid()

    return TestDatatype


# Generate TestCase objects for each datatype wrapper
self = soup.get_module(__name__)
for wrapper in soup.data.get_all():
    testklass = make_testcase(wrapper)
    setattr(self, testklass.name(), testklass)


# Allow people to run the test case directly
if __name__ == "__main__":
    import unittest
    unittest.main()
