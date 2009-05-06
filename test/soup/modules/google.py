
import soup
import soup.modules

from soup import Online
from soup.data.contact import ContactWrapper
from soup.data.event import EventWrapper

import conduit.modules.GoogleModule.GoogleModule as GoogleModule

class GoogleContacts(soup.modules.ModuleWrapper):

    requires = [Online]
    klass = GoogleModule.ContactsTwoWay
    dataclass = ContactWrapper

    def create_dataprovider(self):
        return self.klass()


class GoogleCalendar(soup.modules.ModuleWrapper):

    requires = [Online]
    klass = GoogleModule.GoogleCalendarTwoWay
    dataclass = EventWrapper

    def create_dataprovider(self):
        return self.klass()

