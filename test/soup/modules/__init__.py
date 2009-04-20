import os, sys


class ModuleWrapper(object):

    def __init__(self, conduit):
        self.conduit = conduit
        self.dp = self.create_dataprovider()

    def get_num_items(self):
        count = 0
        try:
            self.dp.module.refresh()
            count = self.dp.module.get_num_items()
        finally:
            self.dp.module.finish()
        return count

    def get(self, uid):
        return self.dp.module.get(uid)

    def add(self, obj):
        self.dp.module.put(obj, False)

    def update(self, uid, obj):
        self.dp.module.put(obj, True, LUID=uid)

    def delete(self, uid):
        self.dp.module.delete(uid)

    def apply_changes(self, uid):
        for t, uid, obj in changes:
            if t == CHANGE_ADD:
                self.add(obj)
            elif t == CHANGE_REPLACE:
                self.replace(uid, obj)
            elif t == CHANGE_DELETE:
                self.delete(uid)


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
    return ModuleWrapper.__subclasses__()

