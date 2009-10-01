import glib

class WaitOnSignal(object):

    def __init__(self):
        self.context = glib.MainContext()
        self.loop = glib.MainLoop()

    def block(self):
        self.loop.run()

    def unblock(self):
        self.loop.quit()

