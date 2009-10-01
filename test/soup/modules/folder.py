import soup.modules
from soup.data.file import FileWrapper

import conduit.modules.FileModule.FileModule as FileModule
import conduit.utils as Utils

import shutil

class Folder(soup.modules.ModuleWrapper):

    klass = FileModule.FolderTwoWay
    dataclass = FileWrapper

    def create_dataprovider(self):
        self.folder = Utils.new_tempdir()
        dp = self.klass()
        dp.set_configuration({
            "folder": self.folder,
        })
        return dp

    def destroy_dataprovider(self):
        shutil.rmtree(self.folder)

