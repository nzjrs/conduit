import soup

import conduit.utils as Utils
from conduit.datatypes import Event

import datetime

class EventWrapper(soup.data.DataWrapper):

    wraps = Event.Event

    def iter_samples(self):
        for f in self.get_files_from_data_dir("*.ical"):
            txt = open(f).read()
            e = Event.Event()
            e.set_from_ical_string(txt)
            e.set_mtime(datetime.datetime.now())
            e.set_UID(Utils.random_string())
            yield e

    def generate_sample(self):
        pass

