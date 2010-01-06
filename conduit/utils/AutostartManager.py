import os.path
import logging
log = logging.getLogger("Utils.Autostart")

import conduit

class AutostartManager:
    def __init__(self):
        self._file = os.path.join(conduit.AUTOSTART_FILE_DIR, "conduit.desktop")

    def is_start_at_login_enabled(self):
        if os.path.exists(self._file):
            #if it contains X-GNOME-Autostart-enabled=false then it has
            #has been disabled by the user in the session applet, otherwise
            #it is enabled
            return open(self._file).read().find("X-GNOME-Autostart-enabled=false") == -1
        else:
            return False

    def update_start_at_login(self, update):
        desktopFile = os.path.join(conduit.DESKTOP_FILE_DIR, "conduit.desktop")

        if os.path.exists(self._file):
            log.info("Removing autostart desktop file")
            os.remove(self._file)

        if update:
            if not os.path.exists(desktopFile):
                log.critical("Could not find conduit desktop file: %s" % desktopFile)
                return

            log.info("Adding autostart desktop file")
            #copy the original file to the new file, but 
            #add -i to the exec line (start iconified)
            old = open(desktopFile, "r")
            new = open(self._file, "w")

            for l in old.readlines():         
                if l.startswith("Exec="):
                    new.write(l[0:-1])
                    new.write(" -i\n")
                else:
                    new.write(l)

            old.close()
            new.close()

