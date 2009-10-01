import soup

import conduit.utils as Utils
from conduit.datatypes import Text

import datetime

class TextWrapper(soup.data.DataWrapper):

    wraps = Text.Text

    def iter_samples(self):
        #FIXME: This is not very useful
        for f in self.get_files_from_data_dir("*.ical"):
            t = Text.Text(text=open(f).read())
            t.set_mtime(datetime.datetime.now())
            t.set_UID(Utils.random_string())
            yield t

    def generate_sample(self):
        t = Text.Text(text=Utils.random_string())
        t.set_mtime(datetime.datetime.now())
        t.set_UID(Utils.random_string())
        return t
