import soup.modules
from soup.data.file import FileWrapper

import conduit.modules.FileModule.FileModule as FileModule
import conduit.utils as Utils


class Folder(soup.modules.ModuleWrapper):

    klass = FileModule.FolderTwoWay
    dataclass = FileWrapper

    def create_dataprovider(self):
        dp = self.klass()
        dp.set_configuration({
            "folder": Utils.new_tempdir(),
        })
        return dp

