
import soup
import soup.modules

from soup.data.note import NoteWrapper
from soup.data.contact import ContactWrapper
from soup.data.event import EventWrapper

import conduit.modules.EvolutionModule.EvolutionModule as EvolutionModule

class EvolutionMemo(soup.modules.ModuleWrapper):

    klass = EvolutionModule.EvoMemoTwoWay
    dataclass = NoteWrapper

    def create_dataprovider(self):
        return self.klass()


class EvolutionContacts(soup.modules.ModuleWrapper):

    klass = EvolutionModule.EvoContactTwoWay
    dataclass = ContactWrapper

    def create_dataprovider(self):
        return self.klass()


class EvolutionCalendar(soup.modules.ModuleWrapper):

    klass = EvolutionModule.EvoCalendarTwoWay
    dataclass = EventWrapper

    def create_dataprovider(self):
        return self.klass()


class EvolutionTasks(soup.modules.ModuleWrapper):

    klass = EvolutionModule.EvoTasksTwoWay
    dataclass = EventWrapper

    def create_dataprovider(self):
        return self.klass()

