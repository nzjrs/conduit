import soup

import conduit.utils as Utils
from conduit.datatypes import Setting

import datetime

class SettingWrapper(soup.data.DataWrapper):

    wraps = Setting.Setting

    def iter_samples(self):
        #FIXME: Would be nice to have some actual settings.
        for i in range(5):
            yield self.generate_sample()

    def generate_sample(self):
        s = Setting.Setting(key=Utils.random_string(), value=Utils.random_string())
        s.set_mtime(datetime.datetime.now())
        s.set_UID(Utils.random_string())
        return s
