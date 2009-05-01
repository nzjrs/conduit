import os, sys


class ModuleWrapper(object):

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

    def update(self, uid, obj):
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

def load_modules():
    basepath = os.path.dirname(__file__)
    for root, dirs, files in os.walk(basepath):
        for dir in dirs:
            if dir[:1] != ".":
                load_module(dir)
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                load_module(file[:-3])
        break

def load_module(module):
    if sys.modules.has_key(module):
        reload(sys.modules[module])
    else:
        __import__("soup.modules", {}, {}, [module])

def get_all():
    if len(ModuleWrapper.__subclasses__()) == 0:
        load_modules()
    return ModuleWrapper.__subclasses__()

