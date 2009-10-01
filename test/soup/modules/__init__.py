import os, sys

from soup.utils.pluginloader import PluginLoader

class ModuleWrapper(object):

    requires = []

    def __init__(self, conduit):
        self.conduit = conduit
        self.dp = self.create_dataprovider()

    @classmethod
    def name(cls):
        return cls.__name__

    def get_num_items(self):
        count = 0
        try:
            self.dp.refresh()
            count = self.dp.get_num_items()
        finally:
            self.dp.finish(False, False, False)
        return count

    def get_all(self):
        self.dp.refresh()
        return self.dp.get_all()

    def get(self, uid):
        return self.dp.get(uid)

    def add(self, obj):
        self.dp.put(obj, False)

    def replace(self, uid, obj):
        self.dp.put(obj, True, LUID=uid)

    def delete(self, uid):
        self.dp.delete(uid)

    def delete_all(self):
        for uid in self.get_all():
            self.delete(uid)

    def apply_changes(self, uid):
        for t, uid, obj in changes:
            if t == CHANGE_ADD:
                self.add(obj)
            elif t == CHANGE_REPLACE:
                self.replace(uid, obj)
            elif t == CHANGE_DELETE:
                self.delete(uid)

    @classmethod
    def is_twoway(cls):
        return cls.klass._module_type_ == "twoway"

    def get_wrapped(self):
        return self.conduit.wrap_dataprovider(self.dp)

class _ModuleLoader(PluginLoader):
    _subclass_ = ModuleWrapper
    _module_ = "soup.modules"
    _path_ = os.path.dirname(__file__)

ModuleLoader = _ModuleLoader()

