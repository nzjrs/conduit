import soup

import conduit.utils as Utils
from conduit.datatypes import Contact

import datetime

class ContactWrapper(soup.data.DataWrapper):

    wraps = Contact.Contact

    def iter_samples(self):
        for f in self.get_files_from_data_dir("*.vcard"):
            txt = open(f).read()
            c = Contact.Contact()
            c.set_from_vcard_string(txt)
            c.set_mtime(datetime.datetime.now())
            c.set_UID(Utils.random_string())
            yield c

    def generate_sample(self):
        pass
