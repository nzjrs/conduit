
import soup

from soup.data.note import NoteWrapper

import conduit.modules.TomboyModule as TomboyModule

class Tomboy(soup.modules.ModuleWrapper):

    klass = TomboyModule.TomboyNoteTwoWay
    dataclass = NoteWrapper

    def create_dataprovider(self):
        return self.klass()

    def destroy_dataprovider(self):
        pass
