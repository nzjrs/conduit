
import soup.modules

class iPodCalendar(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = Utils.new_tempdir()
        return None

