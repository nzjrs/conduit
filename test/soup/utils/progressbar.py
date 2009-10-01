
import os
import sys
import signal
import termios
from fcntl import ioctl
from array import array


class Widget(object):

    def __init__(self, pb, next=None):
        self.pb = pb
        self.next = next

    def update(self):
        raise NotImplementedError

    def finish(self):
        return ""


class SimpleWidget(Widget):

    def update(self, pb):
        return "%d of %d" % (pb.cur, pb.max)


class BarWidget(Widget):

    left = "["
    right = "]"

    def update(self):
        progress_space = self.pb.term_width - len(self.left) - len(self.right)
        number_of_frobs = self.pb.cur * progress_space / self.pb.max
        number_of_spaces = progress_space - number_of_frobs
        return self.left + "*" * number_of_frobs + " " * number_of_spaces + self.right

    def finish(self):
        return "\r%s\r" % (self.pb.term_width * " ")


class ProgressBar(object):

    def __init__(self):
        self.max = 100
        self.cur = 0

        self.f = sys.stderr

        try:
            self._handle_resize(None, None)
            signal.signal(signal.SIGWINCH, self._handle_resize)
        except:
            self.term_width = int(os.environ.get('COLUMNS', 80)) - 1

        self.widget = BarWidget(self)

    def _handle_resize(self, signum, frame):
        h, w = array('h', ioctl(self.f, termios.TIOCGWINSZ, '\0' * 8))[:2]
        self.term_width = w

    def update(self, cur):
        self.cur = cur
        self.f.write(self.widget.update() + '\r')

    def finish(self):
        self.widget.finish()

