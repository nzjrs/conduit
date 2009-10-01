
import soup
import soup.modules

from soup.data.file import FileWrapper
from soup.utils.test import Online

import conduit.modules.FeedModule.FeedModule as FeedModule
import conduit.utils as Utils

FeedPackages = soup.utils.test.Package("feedparser")

class FeedWrapper(soup.modules.ModuleWrapper):

    klass = FeedModule.RSSSource
    dataclass = FileWrapper
    requires = [FeedPackages, Online]

    def create_dataprovider(self):
        dp = self.klass()
        dp.set_configuration({
            "feedUrl": "http://planet.gnome.org/atom.xml",
            # "limit": 5,
            # "randomize": None,
            "downloadAudio": True,
            "downloadVideo": True,
            "downloadPhotos": True,
        })
        return dp

