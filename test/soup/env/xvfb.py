
import os
import signal
import subprocess
import sys, random, tempfile, time

try:
    from hashlib import md5
except ImportError:
    import md5


import soup


class Xvfb(soup.env.EnvironmentWrapper):

    @classmethod
    def enabled(cls, opts):
        return False

    def _get_display(self):
        servernum = 99
        while True:
            if not os.path.exists('/tmp/.X%d-lock' % servernum):
                break
            servernum += 1
        return str(servernum)

    def _set_xauth(self, servernum):
        paths = os.environ.get('PATH').split(':')
        for path in paths:
            if os.path.exists(os.path.join(path, "xauth")):
                break
        else:
            raise AssertError("Unable to find xauth in PATH")

        jhfolder = os.path.join(tempfile.gettempdir(), 'soup.%d' % os.getpid())
        if os.path.exists(jhfolder):
            raise AssertError("Soup Xvfb folder already exists")

        try:
            os.mkdir(jhfolder)
            new_xauth = os.path.join(jhfolder, 'Xauthority')
            open(new_xauth, 'w').close()
            hexdigest = md5.md5(str(random.random())).hexdigest()
            os.system('xauth -f "%s" add ":%s" "." "%s"' % (
                new_xauth, servernum, hexdigest))
        except OSError:
            raise AssertError("Unable to setup XAuth")

        return new_xauth

    def prepare_environment(self):
        self.old_display = os.environ['DISPLAY']
        self.old_xauth = os.environ['XAUTHORITY']

        self.new_display = self._get_display()
        self.new_xauth = self._set_xauth(self.new_display)

        os.environ['DISPLAY'] = ':' + self.new_display
        os.environ['XAUTHORITY'] = self.new_xauth

        self.xvfb = subprocess.Popen(['Xvfb',':'+self.new_display] + self.config, shell=False)

        #FIXME: Is there a better way??
        time.sleep(2)

        if self.xvfb.poll() != None:
            raise Fail

    def finalize_environment(self):
        if self.xvfb:
            os.kill(self.xvfb.pid, signal.SIGINT)
        if self.new_display:
            os.system('xauth remove ":%s"' % self.new_display)
        if self.new_xauth:
            os.system('rm -r %s' % os.path.split(self.new_xauth)[0])

        if self.old_display:
            os.environ['DISPLAY'] = self.old_display
        else:
            del os.environ['DISPLAY']

        if self.old_xauth:
            os.environ['XAUTHORITY']
        else:
            del os.environ['XAUTHORITY']

