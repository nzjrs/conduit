
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
        return iPodModule.IPodNoteTwoWay(self.folder, "")


class iPodContacts(soup.modules.ModuleWrapper):

    dataclass = ContactWrapper

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        return iPodModule.IPodContactsTwoWay(self.folder, "")


class iPodCalendar(soup.modules.ModuleWrapper):

    dataclass = EventWrapper

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        return iPodModule.IPodCalendarTwoWay(self.folder, "")


class iPodPhoto(soup.modules.ModuleWrapper):

    dataclass = PhotoWrapper

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        return iPodModule.IPodPhotoSink(self.folder, "")


class iPodMusic(soup.modules.ModuleWrapper):

    dataclass = MusicWrapper

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        return iPodModule.IPodMusicTwoWay(self.folder, "")

