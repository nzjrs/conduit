import soup
from soup.modules import ModuleLoader

def make_testcase(wrp):
    class TestDataprovider(soup.utils.test.TestCase):
        wrapperclass = wrp

        @classmethod
        def name(self):
            return "TestDataProvider%s" % self.wrapperclass.name()

        def requires(self):
            return self.wrapperclass.requires

        def setUp(self):
            super(TestDataprovider, self).setUp()
            self.wrapper = self.wrapperclass(self)
            self.dp = self.wrapper.dp
            self.data = self.wrapper.dataclass()

        def tearDown(self):
            self.wrapper.destroy_dataprovider()

        def test_add(self):
            """ Should be able to add items """
            self.dp.refresh()
            count = 0
            for obj in self.data.iter_samples():
                count += 1
                self.dp.put(obj, False, None)
            self.dp.finish(False, False, False)
            assert self.wrapper.get_num_items() == count

        def test_replace(self):
            """ Should be able to replace items """
            obj = self.data.iter_samples().next()
            self.dp.refresh()
            rid = self.dp.put(obj, False, None)
            self.dp.finish(False, False, False)
            assert self.wrapper.get_num_items() == 1

            self.dp.refresh()
            self.dp.put(obj, True, rid.get_UID())
            self.dp.finish(False, False, False)
            assert self.wrapper.get_num_items() == 1

        def test_delete(self):
            """ Should be able to delete items """
            obj = self.data.iter_samples().next()
            self.dp.refresh()
            rid = self.dp.put(obj, False, None)
            self.dp.finish(False, False, False)

            assert self.wrapper.get_num_items() == 1

            self.dp.refresh()
            self.dp.delete(rid.get_UID())
            self.dp.finish(False, False, False)
            assert self.wrapper.get_num_items() == 0

        def test_refresh(self):
            """ Refresh shouldnt throw exceptions """
            self.dp.refresh()
            self.dp.finish(False, False, False)

        def test_finish(self):
            """ Should be able to call finish on cold """
            self.dp.finish(False, False, False)

        def test_get_num_items(self):
            """ Number of items in a fresh dataprovider should be 0 """
            self.dp.refresh()
            assert self.dp.get_num_items() == 0

    return TestDataprovider


# Generate TestCase objects for each dataprovider wrapper
self = soup.get_module(__name__)
for wrapper in ModuleLoader.get_all():
    if wrapper.is_twoway():
        testklass = make_testcase(wrapper)
        setattr(self, testklass.name(), testklass)


# Allow people to run the test case directly
if __name__ == "__main__":
    import unittest
    unittest.main()
