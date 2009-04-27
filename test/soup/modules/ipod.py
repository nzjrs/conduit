
import soup
import soup.modules

from soup.data.note import NoteWrapper
from soup.data.contact import ContactWrapper
from soup.data.event import EventWrapper
from soup.data.photo import PhotoWrapper
from soup.data.music import MusicWrapper

import conduit.modules.iPodModule.iPodModule as iPodModule
import conduit.utils as Utils

import gpod

def create_fake_ipod():
    dir = Utils.new_tempdir()
    assert gpod.gpod.itdb_init_ipod(dir, "MA450", "Test iPod", None)
    return dir


class iPodNote(soup.modules.ModuleWrapper):

    dataclass = NoteWrapper

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        ipod = iPodModule.IPodNoteTwoWay(self.folder, "")
        return self.conduit.wrap_dataprovider(ipod)


class iPodContacts(soup.modules.ModuleWrapper):

    dataclass = ContactWrapper

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        ipod = iPodModule.IPodContactsTwoWay(self.folder, "")
        return self.conduit.wrap_dataprovider(ipod)


class iPodCalendar(soup.modules.ModuleWrapper):

    dataclass = EventWrapper

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        ipod = iPodModule.IPodCalendarTwoWay(self.folder, "")
        return self.conduit.wrap_dataprovider(ipod)


class iPodPhoto(soup.modules.ModuleWrapper):

    dataclass = PhotoWrapper

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        ipod = iPodModule.IPodPhotoSink(self.folder, "")
        return self.conduit.wrap_dataprovider(ipod)


class iPodMusic(soup.modules.ModuleWrapper):

    dataclass = MusicWrapper

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        ipod = iPodModule.IPodMusicTwoWay(self.folder, "")
        return self.conduit.wrap_dataprovider(ipod)

