import soup

import conduit.utils as Utils
from conduit.datatypes import Email

import datetime

class EmailWrapper(soup.data.DataWrapper):

    wraps = Email.Email

    def iter_samples(self):
        #FIXME: Would be nice to have some actual settings.
        for i in range(5):
            yield self.generate_sample()

    def generate_sample(self):
        e = Email.Email(content=Utils.random_string(), subject=Utils.random_string())
        e.set_mtime(datetime.datetime.now())
        e.set_UID(Utils.random_string())
        return e

