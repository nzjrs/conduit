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

class VolumeMonitor(gobject.GObject):

    __gsignals__ = {
        "volume-mounted" :      (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [
            gobject.TYPE_STRING,        #udi/uuid
            gobject.TYPE_STRING,        #mount point
            gobject.TYPE_STRING]),      #label
        "volume-unmounted" :    (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [
            gobject.TYPE_STRING])       #udi/uuid

    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self._vm = gio.volume_monitor_get()
        self._vm.connect("mount-added", self._mounted_cb)
        self._vm.connect("mount-removed", self._unmounted_cb)

    def _mounted_cb(self, sender, mount):
        self.emit("volume-mounted", 
            mount.get_uuid(),
            mount.get_root().get_uri(),
            mount.get_name())

    def _unmounted_cb(self, sender, mount):
        self.emit("volume-unmounted", mount.get_uuid())

    def get_mounted_volumes(self):
        """
        @returs: Dict of mounted volumes, uuid : (mount, name) 
        """
        vols = {}
        for m in self._vm.get_mounts():
            vols[m.get_uuid()] = (m.get_root().get_uri(), m.get_name())
        return vols

