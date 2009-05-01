
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

class iPodWrapper(object):

    def create_dataprovider(self):
        self.folder = Utils.new_tempdir()
        assert gpod.gpod.itdb_init_ipod(self.folder, "MA450", "Test iPod", None)
        return self.klass(self.folder, "")


class iPodNote(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodNoteTwoWay
    dataclass = NoteWrapper

class iPodContacts(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodContactsTwoWay
    dataclass = ContactWrapper

class iPodCalendar(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodCalendarTwoWay
    dataclass = EventWrapper

class iPodPhoto(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodPhotoSink
    dataclass = PhotoWrapper

class iPodMusic(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodMusicTwoWay
    dataclass = MusicWrapper

