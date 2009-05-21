
import soup

import pdb

class Debugger(soup.env.EnvironmentWrapper):

    @classmethod
    def enabled(cls, opts):
        return opts.debug

    def decorate_test(self, test):
        def _(*args, **kwargs):
            pdb.runcall(test, *args, **kwargs)
        return _

