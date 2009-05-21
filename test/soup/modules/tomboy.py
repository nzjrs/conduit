
import soup

from soup.data.note_tomboy import TomboyNoteWrapper

import conduit.modules.TomboyModule as TomboyModule

import dbus

class Tomboy(soup.modules.ModuleWrapper):

    klass = TomboyModule.TomboyNoteTwoWay
    dataclass = TomboyNoteWrapper

    def create_dataprovider(self):
        a, retval = dbus.SessionBus().start_service_by_name("org.gnome.Tomboy")
        return self.klass()

    def destroy_dataprovider(self):
        pass
