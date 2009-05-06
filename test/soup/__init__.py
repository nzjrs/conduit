
import os, sys
import unittest

def get_root():
    cwd = os.path.dirname(__file__)
    parts = cwd.split(os.path.sep)
    while len(parts) > 0:
        path = os.path.join(os.path.sep, *parts)
        if os.path.isfile(os.path.join(path, 'configure.ac')):
            return path
        parts.pop()
    raise NotImplementedError(get_root)

def get_module(name):
    """ This is just to avoid importing sys everywhere and i want my tests to be pretty! """
    return sys.modules[name]

sys.path.insert(0, get_root())

