
import os
import signal
import subprocess
import tempfile

import soup

class DbusMonitor(soup.env.EnvironmentWrapper):

    @classmethod
    def enabled(cls, opts):
        return False

    def decorate_test(self, test):
        def _(result, *args, **kwargs):
            logfile = tempfile.TemporaryFile()
            p = subprocess.Popen("dbus-monitor", stdout=logfile, stderr=subprocess.STDOUT, close_fds=True)
            test(result, *args, **kwargs)
            os.kill(p.pid, signal.SIGINT)
            logfile.seek(0)
            result.addAttachment(test, "D-Bus Monitor logs", logfile.read())
        return _

