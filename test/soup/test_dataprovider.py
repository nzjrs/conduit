import soup

def make_testcase(wrp):
    class TestDataprovider(soup.TestCase):
        wrapperclass = wrp

        def setUp(self):
            super(TestDataprovider, self).setUp()
            self.wrapper = self.wrapperclass(self)
            self.dp = self.wrapper.dp

        def tearDown(self):
            self.dp = None

        def test_add(self):
            pass

        def test_replace(self):
            pass

        def test_delete(self):
            pass

        def test_refresh(self):
            pass

        def test_finish(self):
            self.dp.module.finish(None, None, None)

        def test_get_num_items(self):
            #self.dp.refresh()
            #assert self.dp.get_num_items() == 0
            pass

    return TestDataprovider


# Generate TestCase objects for each dataprovider wrapper
self = soup.get_module(__name__)
for wrapper in soup.modules.get_all():
    setattr(self, "TestDataprovider%s" % wrapper.name(), make_testcase(wrapper))


# Allow people to run the test case directly
if __name__ == "__main__":
    import unittest
    unittest.main()
