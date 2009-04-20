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


# Generate TestCase objects for each dataprovider wrapper
self = soup.get_module(__name__)
for wrapper in soup.modules.get_all():
    setattr(self, "TestDataprovider%s" % "Folder", make_testcase(wrapper))


# Allow people to run the test case directly
if __name__ == "__main__":
    import unittest
    unittest.main()
