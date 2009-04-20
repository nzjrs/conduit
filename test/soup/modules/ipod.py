
import soup.modules

import conduit.modules.iPodModule.iPodModule as iPodModule
import conduit.utils as Utils

def create_fake_ipod():
    dir = Utils.new_tempdir()
    # create fake directory structure here...
    return dir


class iPodNote(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        return iPodModule.IPodNoteTwoWay(self.folder, "")


class iPodContacts(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        return iPodModule.IPodContactsTwoWay(self.folder, "")


class iPodCalendar(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        return iPodModule.IPodCalendarTwoWay(self.folder, "")


class iPodPhoto(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        photodp = iPodModule.IPodPhotoSink(self.folder, "")
        photodp._set_sysinfo("ModelNumStr", "MA450")
        return photodp


class iPodMusic(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        return iPodModule.IPodMusicTwoWay(self.folder, "")

