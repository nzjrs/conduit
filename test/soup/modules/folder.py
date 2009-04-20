import soup.modules

import conduit.utils as Utils

class Folder(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        dp = self.conduit.get_dataprovider("FolderTwoWay")
        dp.module.set_configuration({
            "source": Utils.new_tempdir(),
        })
        return dp

