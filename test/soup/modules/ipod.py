
import soup.modules

import conduit.utils as Utils

class iPodCalendar(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = Utils.new_tempdir()
        return None

