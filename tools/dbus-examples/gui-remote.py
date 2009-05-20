import gtk
import sys
import getopt
import os
import dbus, dbus.glib

try:
    import libconduit
except ImportError:
    import conduit.libconduit as libconduit

class UI:
    def __init__(self):
        self.app = libconduit.ConduitApplicationWrapper(
                            conduitWrapperKlass=libconduit.ConduitWrapper,
                            addToGui=True,
                            store=False,
                            debug=False)

        w = gtk.Window()
        vb = gtk.VBox()
        w.add(vb)

        #create UI, two combo boxes with dataproviders, and some buttons
        self._dpmodel = gtk.ListStore(str, str)
        vb.pack_start(gtk.Label("Source:"), False, False)
        self._source = self._make_combo()
        vb.pack_start(self._source, False, False)
        vb.pack_start(gtk.Label("Sink:"), False, False)
        self._sink = self._make_combo()
        vb.pack_start(self._sink, False, False)

        conn = gtk.Button("Connect")
        conn.connect("clicked", self._on_connect)
        vb.pack_start(conn, False, False)

        conf = gtk.Button("Configure")
        conf.connect("clicked", self._on_configure)
        vb.pack_start(conf, False, False)

        sync = gtk.Button("Synchronize")
        sync.connect("clicked", self._on_sync)
        vb.pack_start(sync, False, False)

        w.connect('destroy', self._on_quit)
        w.set_default_size(300,-1)
        w.show_all()

    def _make_combo(self):
        cb = gtk.ComboBox(self._dpmodel)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        return cb

    def _on_connect(self, btn):
        if self.app.connect_to_conduit(startConduit=False):
            self._dpmodel.clear()
            for name,key in self.app.get_dataproviders().items():
                self._dpmodel.append((name, key))
            for row in self._dpmodel:
                if row[0] == "TestSource":
                    self._source.set_active_iter(row.iter)
                if row[0] == "TestSink":
                    self._sink.set_active_iter(row.iter)
            btn.set_label("Connected")

    def _on_configure(self, btn):
        if self.app.connected():
            #build the dataprovider
            pass

    def _on_sync(self, btn):
        pass

    def _on_quit(self, *args):
        gtk.main_quit()

if __name__ == "__main__":
    u = UI()
    gtk.main()   


