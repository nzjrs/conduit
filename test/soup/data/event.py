import soup

import conduit.utils as Utils
from conduit.datatypes import Event

class EventWrapper(soup.data.DataWrapper):

    def iter_samples(self):
        for f in self.get_files_from_data_dir("*.ical"):
            txt = open(f).read()
            e = Event.Event()
            e.set_from_ical_string(txt)
            e.set_UID(Utils.random_string())
            yield e

    def generate_sample(self):
        pass

