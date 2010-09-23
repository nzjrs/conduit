"""
Copyright: Alexandre Rosenfeld, 2009
License: GPLv2
"""
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle

class Error(Exception):
    '''
    Base exception for errors in the cache.
    '''
    pass

class ModuleCache(object):
    def __init__(self, filename):
        self.filename = filename
        self.cached_modules = {}
        self.modules = {}
        
    def add_modules(self, filename, modules):
        self.modules[filename] = {'modules': modules,
                                  'mtime': os.stat(filename).st_mtime}

    def is_valid(self, filename):
        return (filename in self.cached_modules and self.cached_modules[filename]['mtime'] == os.stat(filename).st_mtime)
        
    def get_modules(self, filename):
        self.modules[filename] = self.cached_modules[filename]
        return self.cached_modules[filename]['modules']

    def load(self):
        if os.path.exists(self.filename):
            log.critical("No modules cache found")
            return False    
        cache_file = open(self.filename, "rb")
        try:
            self.cached_modules = pickle.load(cache_file)
            #We check all the contents so we dont load an invalid cache
            if not isinstance(self.cached_modules, dict):
                raise Error("Cache is not a dict")
            for key, value in self.cached_modules.iteritems():
                if not isinstance(key, basestring):
                    raise Error("%s not a string" % key)
                if not isinstance(value, dict):
                    raise Error("%s not a dict" % value)
            return True
        except Error, e:
            log.warn("Modules cache invalid (%s)" % e.message)
            self.cached_modules = {}
            return False
        finally:
            cache_file.close()                

    def save(self):
        if self.cached_modules == self.modules:
            return False
        #log.critical("Saving cache")
        cache_file = open(self.filename, "wb")
        try:
            pickle.dump(self.modules, cache_file)
        finally:
            cache_file.close()
        self.cached_modules = self.modules
        return True
