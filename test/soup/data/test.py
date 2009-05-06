import soup

import conduit.utils as Utils
from conduit.modules import TestModule

import datetime

class TestDataTypeWrapper(soup.data.DataWrapper):

    wraps = TestModule.TestDataType

    def iter_samples(self):
        #FIXME: Would be nice to have some actual settings.
        for i in range(5):
            yield self.generate_sample()

    def generate_sample(self):
        t = TestModule.TestDataType(Utils.random_string())
        t.set_mtime(datetime.datetime.now())
        t.set_UID(Utils.random_string())
        return t
