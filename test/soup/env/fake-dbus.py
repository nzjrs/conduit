
import os
import signal
import subprocess
import tempfile

import soup

# FIXME: Something somewhere is causing us to poke libdbus into looking at DBUS_SESSION_BUS_ADDRESS early
# The official answer is that soup is evil :'(
# 1. Envrionment code should run as early as possible (before test loader)
# 2. Should avoid doing too much crack on import :/

class Dbus(soup.env.EnvironmentWrapper):

    @classmethod
    def enabled(cls, opts):
        return False

    def prepare_environment(self):
        conffile = os.path.join(os.path.dirname(__file__), "fake-session-bus.conf")
        daemonargs = ['dbus-daemon', '--fork', '--config-file=%s' % conffile, '--print-pid=1', '--print-address=1']

        #FIXME: Probably belongs in build system, but at same time i dont want to depend on a damned build system :)
        open(conffile,'w').write(open(conffile+'.in','r').read().replace('@top_builddir@', soup.get_root()))

        # start our own dbus daemon :) :)
        dbus = subprocess.Popen(daemonargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = dbus.communicate()

        # make sure we have something like what a proper daemon would give us...
        daemon_resp = out.split()
        assert len(daemon_resp) == 2
        assert daemon_resp[0].startswith('unix:abstract=')
        assert daemon_resp[1].isdigit()

        self.address, self.pid = daemon_resp

        # lets use this session bus when we run tests
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = self.address

    def decorate_test(self, test):
        def _(*args, **kwargs):
            fd, f = tempfile.mkstemp()
            os.close(fd)
            p = subprocess.Popen("dbus-monitor &> %s" % f, shell=True)
            test(*args, **kwargs)
            os.kill(p.pid, signal.SIGINT)
            # FIXME: Need some way to attach data to a test
            # print open(f).read()
            os.unlink(f)
        return _

    def finalize_environment(self):
        os.kill(int(self.pid), signal.SIGINT)

