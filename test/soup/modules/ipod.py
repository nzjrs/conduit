
import soup
import soup.modules

from soup.data.note import NoteWrapper
from soup.data.contact import ContactWrapper
from soup.data.event import EventWrapper
from soup.data.photo import PhotoWrapper
from soup.data.music import MusicWrapper
from soup.data.video import VideoWrapper

import conduit.modules.iPodModule.iPodModule as iPodModule
import conduit.utils as Utils

import uuid
import shutil

GpodModule = soup.utils.test.Package("gpod")

class iPodWrapper(object):
    def create_dataprovider(self):
        import gpod
        self.folder = Utils.new_tempdir()
        assert gpod.gpod.itdb_init_ipod(self.folder, "MA450", "Test iPod", None)
        return self.klass(self.folder, str(uuid.uuid4()))

    def destroy_dataprovider(self):
        shutil.rmtree(self.folder)

class iPodNote(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodNoteTwoWay
    dataclass = NoteWrapper
    requires = [GpodModule]

class iPodContacts(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodContactsTwoWay
    dataclass = ContactWrapper
    requires = [GpodModule]

class iPodCalendar(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodCalendarTwoWay
    dataclass = EventWrapper
    requires = [GpodModule]

class iPodPhoto(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodPhotoSink
    dataclass = PhotoWrapper
    requires = [GpodModule]

class iPodMusic(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodMusicTwoWay
    dataclass = MusicWrapper
    requires = [GpodModule]

class iPodVideo(soup.modules.ModuleWrapper, iPodWrapper):
    klass = iPodModule.IPodVideoTwoWay
    dataclass = VideoWrapper
    requires = [GpodModule]

