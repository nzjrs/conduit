import gobject
import gudev

import logging
log = logging.getLogger("utils.UDev")

class UDevHelper(gudev.Client):
    def __init__(self, *subsystems):
        gudev.Client.__init__(self, subsystems)
        self._subsystems = subsystems

    def query_by_subsystems(self, *subsystems):
        if not subsystems:
            subsystems = self._subsystems
        devices = []
        for s in subsystems:
            devices.extend( self.query_by_subsystem(s) )
        return devices

    def get_device_properties(self, device):
        props = {}
        for key in device.get_property_keys():
            props[key.upper()] = device.get_property(key)
        return props

