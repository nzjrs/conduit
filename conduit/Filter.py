"""
Represents a filter (an operation applied to the output of a Conduit)

Copyright: John Stowers, 2009
License: GPLv2
"""
import gobject
import logging
log = logging.getLogger("Filter")

import conduit
import conduit.utils as Utils

class Filter:
    def __init__(self):
        pass

    def apply_filter(self, items):
        return items
