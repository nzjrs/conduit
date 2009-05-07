
import os
import signal
import subprocess

import soup


class Dbus(soup.env.EnvironmentWrapper):

    @classmethod
    def enabled(cls, opts):
        return True

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

    def finalize_environment(self):
        os.kill(int(self.pid), signal.SIGINT)

