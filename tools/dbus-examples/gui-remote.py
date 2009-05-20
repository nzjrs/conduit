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
        self._source = self._make_combo()
        vb.pack_start(self._source, False, False)
        self._sink = self._make_combo()
        vb.pack_start(self._sink, False, False)

        conn = gtk.Button("Connect")
        conn.connect("clicked", self._on_connect)
        vb.pack_start(conn, False, False)

        conf = gtk.Button("Configure")
        conf.connect("clicked", self._on_connect)
        vb.pack_start(conf, False, False)

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
            btn.set_label("Connected")

    def _on_configure(self, btn):
        if self.app.connected():
            #build the dataprovider
            pass

if __name__ == "__main__":
    u = UI()
    gtk.main()   


