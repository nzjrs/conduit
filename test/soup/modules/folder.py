import soup.modules
from soup.data.file import FileWrapper

import conduit.utils as Utils


class Folder(soup.modules.ModuleWrapper):

    dataclass = FileWrapper

    def create_dataprovider(self):
        dp = self.conduit.get_dataprovider("FolderTwoWay")
        dp.module.set_configuration({
            "folder": Utils.new_tempdir(),
        })
        return dp

