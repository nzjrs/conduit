
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
        ipod = iPodModule.IPodNoteTwoWay(self.folder, "")
        return self.conduit.wrap_dataprovider(ipod)


class iPodContacts(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        ipod = iPodModule.IPodContactsTwoWay(self.folder, "")
        return self.conduit.wrap_dataprovider(ipod)


class iPodCalendar(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        ipod = iPodModule.IPodCalendarTwoWay(self.folder, "")
        return self.conduit.wrap_dataprovider(ipod)


class iPodPhoto(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        photodp = iPodModule.IPodPhotoSink(self.folder, "")
        photodp._set_sysinfo("ModelNumStr", "MA450")
        return self.conduit.wrap_dataprovider(photodp)


class iPodMusic(soup.modules.ModuleWrapper):

    def create_dataprovider(self):
        self.folder = create_fake_ipod()
        ipod = iPodModule.IPodMusicTwoWay(self.folder, "")
        return self.conduit.wrap_dataprovider(photodp)

