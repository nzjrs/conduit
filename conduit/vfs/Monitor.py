import gio
import gobject
import logging
log = logging.getLogger("vfs.FileMonitor")

class FileMonitor(gobject.GObject):

    __gsignals__ = {
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [
            gobject.TYPE_PYOBJECT,      #uri that changed
            gobject.TYPE_PYOBJECT])     #event type
        }

    MONITOR_EVENT_CREATED =             gio.FILE_MONITOR_EVENT_CREATED
    MONITOR_EVENT_CHANGED =             gio.FILE_MONITOR_EVENT_CHANGED
    MONITOR_EVENT_DELETED =             gio.FILE_MONITOR_EVENT_DELETED
    MONITOR_DIRECTORY =                 255

    def __init__(self):
        gobject.GObject.__init__(self)
        self._fm = None

    def _on_change(self, monitor, f1, f2, event):
        self.emit("changed", f1.get_uri(), event)

    def add(self, URI, monitorType):
        try:
            if monitorType == self.MONITOR_DIRECTORY:
                self._fm = gio.File(URI).monitor_directory()
            else:
                self._fm = gio.File(URI).monitor_file()

            self._fm.connect("changed", self._on_change)
        except gio.Error:
            log.warn("Could not add monitor", exc_info=True)

    def cancel(self):
        if self._fm:
            try:
                self._fm.disconnect_by_func(self._on_change)
            except TypeError:
                pass


