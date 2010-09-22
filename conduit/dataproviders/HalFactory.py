import gobject
import gudev
import gio

import logging
log = logging.getLogger("dataproviders.HalFactory")

import conduit.utils as Utils
import conduit.utils.UDev as UDev
import conduit.dataproviders.SimpleFactory as SimpleFactory

log.info("Module Information: %s" % Utils.get_module_information(gudev, "__version__"))

class HalFactory(SimpleFactory.SimpleFactory):

    SUBSYSTEMS = ("usb", "block")

    def __init__(self, **kwargs):
        SimpleFactory.SimpleFactory.__init__(self, **kwargs)

        assert hasattr(self.SUBSYSTEMS, "__iter__")

        self.gudev = UDev.UDevSingleton(self.SUBSYSTEMS)
        self.gudev.connect("uevent", self._on_uevent)
        self.vm = gio.volume_monitor_get()

    def _print_device(self, device):
        return

        print "subsystem", device.get_subsystem()
        print "devtype", device.get_devtype()
        print "name", device.get_name()
        print "number", device.get_number()
        print "sysfs_path:", device.get_sysfs_path()
        print "driver:", device.get_driver()
        print "action:", device.get_action()
        print "seqnum:", device.get_seqnum()
        print "device type:", device.get_device_type()
        print "device number:", device.get_device_number()
        print "device file:", device.get_device_file()
        print "device file symlinks:", ", ".join(device.get_device_file_symlinks())
        print "device keys:", ", ".join(device.get_property_keys())
        for device_key in device.get_property_keys():
            print "   device property %s: %s"  % (device_key, device.get_property(device_key))

    def _on_uevent(self, client, action, device):
        self._print_device(device)
        if action == "add":
            log.debug("Device added")
            self._maybe_new(device)
        elif action == "change":
            log.debug("Device changed")
            self._maybe_new(device)
        elif action == "remove":
            log.debug("Device removed")
            sysfs_path = self.get_sysfs_path_for_device(device)
            self.item_removed(sysfs_path)
        else:
            log.info("Device unknown action: %s" % action)

    def _get_device_properties(self, device):
        props = {}
        for key in device.get_property_keys():
            props[key.upper()] = device.get_property(key)
        return props

    def _maybe_new(self, device):
        props = self._get_device_properties(device)
        sysfs_path = self.get_sysfs_path_for_device(device)
        if self.is_interesting(sysfs_path, props):
            self.item_added(sysfs_path, **props)

    def get_udev_device_for_sysfs_path(self, sysfs_path):
        return self.gudev.query_by_sysfs_path(sysfs_path)

    def get_sysfs_path_for_device(self, device):
        return device.get_sysfs_path()

    def probe(self):
        for s in self.SUBSYSTEMS:
            for d in self.gudev.query_by_subsystem(s):
                self._maybe_new(d)

