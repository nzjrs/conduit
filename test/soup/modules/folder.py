import soup.modules

import conduit.utils as Utils

class FolderWrapper(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        dp = self.conduit.get_dataprovider("FolderTwoWay")
        dp.set_configuration({
            "source": Utils.new_tempdir(),
        })
        return dp

