import gtk
import gobject

class InfoBar(gtk.InfoBar):
    def __init__(self, primary_text, secondary_text=None, message_type=gtk.MESSAGE_INFO, buttons=()):
        gtk.InfoBar.__init__(self)

        vbox = gtk.VBox(False, 6)
    
        primary_label = gtk.Label()
        vbox.pack_start(primary_label, True, True, 0)
        primary_label.set_line_wrap(True)
        primary_label.set_alignment(0, 0.5)
        self._primary_label = primary_label

        secondary_label = None
        if secondary_text:
            secondary_label = gtk.Label()
            vbox.pack_start(secondary_label, True, True, 0)
            if buttons:
                secondary_label.set_line_wrap(True)
            secondary_label.set_alignment(0, 0.5)
        self._secondary_label = secondary_label

        self.update_text(primary_text, secondary_text)

        if buttons:
            for name,response_id in buttons:
                self.add_button(name, response_id)

        self.set_message_type(message_type)
        self.get_content_area().pack_start(vbox, False, False)

    def update_text(self, primary_text="", secondary_text=""):
        if primary_text:
            self._primary_label.set_markup("<b>%s</b>" % primary_text)
        if secondary_text and self._secondary_label:
            self._secondary_label.set_markup("<small>%s</small>" % secondary_text)

class MsgAreaController(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        
    def _timeout(self, infobar):
        try:
            self.remove(infobar)
        except:
            pass
        
    def clear(self):
        for i in self.get_children():
            if type(i) == InfoBar:
                self.remove(i)

    def is_showing_message(self):
        return len(self.get_children()) > 0
        
    def new_from_text_and_icon(self, primary, secondary=None, message_type=gtk.MESSAGE_INFO, buttons=(), timeout=0):
        infobar = InfoBar(primary, secondary, message_type, buttons)
        infobar.show_all()
        self.pack_start(infobar, False, True)
        
        if timeout:
            gobject.timeout_add(timeout*1000, self._timeout, infobar)
            
        return infobar

