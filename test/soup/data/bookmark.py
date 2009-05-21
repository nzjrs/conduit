import soup

import conduit.utils as Utils
from conduit.datatypes import Bookmark

import datetime

class BookmarkWrapper(soup.data.DataWrapper):

    wraps = Bookmark.Bookmark

    def iter_samples(self):
        #FIXME: Would be nice to have some actual bookmarks. Maybe awkward ones
        # - unicode, ip addresses, weird encodings (%2F) etc
        for i in range(5):
            yield self.generate_sample()

    def generate_sample(self):
        b = Bookmark.Bookmark(title=Utils.random_string(), uri="http://%s.com/" % Utils.random_string())
        b.set_mtime(datetime.datetime.now())
        b.set_UID(b.get_uri())
        return b
