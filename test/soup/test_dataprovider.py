import unittest

import soup

def make_testcase(dp):
    class TestDataprovider(soup.TestCase):

        dataprovider = dp

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

    return TestDataprovider

from soup.modules import folder
TestDataproviderFolder = make_testcase(folder.FolderWrapper)

if __name__ == "__main__":
    unittest.main()

