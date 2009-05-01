
import soup
import soup.modules

from soup.data.note import NoteWrapper
from soup.data.contact import ContactWrapper
from soup.data.event import EventWrapper

import conduit.modules.EvolutionModule.EvolutionModule as EvolutionModule

class EvolutionMemo(soup.modules.ModuleWrapper):

    dataclass = NoteWrapper

    def create_dataprovider(self):
        return EvolutionModule.EvoMemoTwoWay()


class EvolutionContacts(soup.modules.ModuleWrapper):

    dataclass = ContactWrapper

    def create_dataprovider(self):
        return EvolutionModule.EvoContactTwoWay()


class EvolutionCalendar(soup.modules.ModuleWrapper):

    dataclass = EventWrapper

    def create_dataprovider(self):
        return EvolutionModule.EvoCalendarTwoWay()


class EvolutionTasks(soup.modules.ModuleWrapper):

    dataclass = EventWrapper

    def create_dataprovider(self):
        return EvolutionModule.EvoTasksTwoWay()

