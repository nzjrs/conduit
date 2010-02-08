import gobject
import gudev

import logging
log = logging.getLogger("utils.UDev")

import conduit.utils as Utils
import conduit.utils.Singleton as Singleton

class UDevSingleton(Singleton.Singleton, gudev.Client):
    def __init__(self, *args, **kwargs):
        super(UDevSingleton, self).__init__(*args, **kwargs)
        log.debug("Constructed: %s" % self)
