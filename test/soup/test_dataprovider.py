import unittest

import soup

class TestDataprovider(soup.BaseTest):

    def test_add(self):
        pass

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

class TestDataproviders(unittest.TestSuite):

    def __init__(self, tests=None):
        tests = []
        for mod in soup.modules.all():
            tests.append(TestDataprovider(mod))

        super(TestDataproviders, self).__init__(tests)

