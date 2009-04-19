import unittest

import soup

class DataproviderTest(soup.TestCase):

    def test_add(self):
        assert self.dataprovider != None

    def test_replace(self):
        pass

    def test_delete(self):
        pass

    def test_refresh(self):
        pass

    def test_finish(self):
        pass

    def test_get_num_items(self):
        pass

def test_suite():
    collection = []
    bases = [DataproviderTest]
    for mod in soup.modules.all():
        name = mod.__class__.__name__
        attrs = {
            "dataprovider": mod
        }
        testcase = type(name, bases, attrs)
        suite = TestLoader().loadTestsFromTestCase(testcase)
        collection.append(suite)
    return unittest.TestSuite(collection)

if __name__ == "__main__":
    unittest.main()

