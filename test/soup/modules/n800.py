
import soup
import soup.modules

from soup.data.file import FileWrapper
from soup.data.photo import PhotoWrapper
from soup.data.music import MusicWrapper
from soup.data.video import VideoWrapper

import conduit.modules.N800Module.N800Module as N800Module
import conduit.utils as Utils


class N800Folder(soup.modules.ModuleWrapper):

    dataclass = FileWrapper

    def create_dataprovider(self):
        self.folder = Utils.new_tempdir()
        return N800Module.N800FolderTwoWay(self.folder, "")


class N800Photo(soup.modules.ModuleWrapper):

    dataclass = PhotoWrapper

    def create_dataprovider(self):
        self.folder = Utils.new_tempdir()
        return N800Module.N800PhotoTwoWay(self.folder, "")


#class N800Music(soup.modules.ModuleWrapper):

#    dataclass = MusicWrapper

#    def create_dataprovider(self):
#        self.folder = Utils.new_tempdir()
#        return N800Module.N800MusicTwoWay(self.folder, "")


#class N800Video(soup.modules.ModuleWrapper):

#    dataclass = VideoWrapper

#    def create_dataprovider(self):
#        self.folder = Utils.new_tempdir()
#        return N800Module.N800VideoTwoWay(self.folder, "")


