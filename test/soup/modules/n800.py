
import soup
import soup.modules

from soup.data.file import FileWrapper
from soup.data.photo import PhotoWrapper
from soup.data.music import MusicWrapper
from soup.data.video import VideoWrapper

import conduit.modules.N800Module.N800Module as N800Module
import conduit.utils as Utils

class N800Wrapper(object):

    def create_dataprovider(self):
        self.folder = Utils.new_tempdir()
        return self.klass(self.folder, "")


class N800Folder(soup.modules.ModuleWrapper, N800Wrapper):
    klass = N800Module.N800FolderTwoWay
    dataclass = FileWrapper

class N800Photo(soup.modules.ModuleWrapper, N800Wrapper):
    klass = N800Module.N800PhotoTwoWay
    dataclass = PhotoWrapper

class N800Audio(soup.modules.ModuleWrapper, N800Wrapper):
    klass = N800Module.N800AudioTwoWay
    dataclass = MusicWrapper

#class N800Video(soup.modules.ModuleWrapper, N800Wraooer):
#    klass = N800Module.N800VideoTwoWay
#    dataclass = VideoWrapper


