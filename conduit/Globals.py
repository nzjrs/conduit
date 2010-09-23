"""
Excapsulates those items global to the Conduit process
"""
class Globals:
    def __init__(self):
        #settings is global and initialized early
        self.settings = None

        #to save resources DB, moduleManager and typeConverter are global
        self.moduleManager = None
        self.typeConverter = None
        self.mappingDB = None
        #syncManager provides the single point of cancellation when exiting
        self.syncManager = None

        #the main application
        self.app = None
        #the dbus interface
        self.dbus = None

        #Global cancellation flag
        self.cancelled = False

        #the application main loop
        self.mainloop = None

    def get_all_syncsets(self):
        ss = []
        for s in [self.app.get_syncset()] + [self.dbus.get_syncset()] + self.dbus.get_all_syncsets():
            if s not in ss:
                ss.append(s)
        return ss
