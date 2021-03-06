"""
Gtk implementation to the configuration controller

Copyright: Alexandre Rosenfeld, 2009
License: GPLv2
"""
import sys

import gobject
import gtk
import logging
log = logging.getLogger("gtkui.Config")

from gettext import gettext as _

import conduit.vfs as Vfs

class Error(Exception):
    """Base exception for all exceptions raised in this module."""
    pass

class Section(gobject.GObject):
    def __init__(self, container, title, order, enabled = True):
        '''
        A section containing items and a title
        '''
        gobject.GObject.__init__(self)
        self.container = container
        self.title = title
        self.order = order
        self.items = []
        self.__enabled = enabled
    
    def add_item(self, item):
        ''' Adds an item to this section (this does not update the dialog) '''
        self.items.append(item)
    
    def attach(self, table, row):
        if self.title:
            row += 1
            label = gtk.Label("<b>%s</b>" % (self.title))
            label.set_alignment(0.0, 0.5)
            label.set_use_markup(True)
            table.resize(row, 2)
            table.attach(label, 0, 2, row - 1, row, xoptions = gtk.FILL | gtk.SHRINK, yoptions = 0)
        for item in sorted(self.items, key = lambda item: item.order):
            row = item._attach(table, row, bool(self.title))
        return row
    
    enabled = property(lambda self: self.__enabled, 
                       lambda self, v: self.set_enabled(v))        
    
    def set_enabled(self, enabled):
        '''
        When enabled, widgets inside this section can be clicked or modified
        '''
        for item in self.items:
            item.set_enabled(enabled)
        self.__enabled = enabled
            
    def apply(self):
        self.container.apply_config(sections = [self])
        
class ItemMeta(gobject.GObjectMeta):
    '''
    Meta class to automatically register item classes.
    
    Based on http://www.djangosnippets.org/snippets/542/
    '''
    def __init__(cls, name, bases, attrs):
        gobject.GObjectMeta.__init__(cls, name, bases, attrs)
        if not hasattr(cls, 'items'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.items = {}
        else:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            if hasattr(cls, '__item_name__'):
                cls.items[cls.__item_name__] = cls
        
class ItemBase(gobject.GObject):
    '''
    A config item is basically a wrapper to a widget.
    
    It works by exposing a value that should be translated to the underlying
    widget. The type of the value depends on the item.
    
    Subclasses should implement _build_widget, _set_value and _get_value.
    If they include choices, they also must implement _set_choices or 
    _clear_choices and _build_choices.
    
    Signals emitted:
        :value-changed: Emitted everytime the value changes. It's signature
            is ``function(is_initial_value, value)`` or 
            ``method(self, is_initial_value, value)``. See the is_initial_value
            function below.
    '''
    __metaclass__ = ItemMeta
    
    __gsignals__ = {
        'value-changed': (gobject.SIGNAL_RUN_FIRST, None, [bool, object]),
    }
    
    def __init__(self, container, title, order, config_name = None,
        config_type = None, choices = None, needs_label = True,
        needs_space = None, initial_value = None, initial_value_callback = None,
        save_callback = None, fill = False, enabled = True, disable_check = False,
        disabled_value = None):
        '''
        Creates a config item.
        
        The parameters customize how the item behaves and/or looks:
        @param config_name: Used in the configuration dict that saves and restores
            this item value.
        @param config_type: ``function(value)`` that converts the config value into
            something a dataprovider will accept. This could be something 
            like int, str, etc., or a custom function.
        @param initial_value: When the item is created or cancel is called,
            the item returns to this value. Changes to the current value
            when apply is called.
        @param initial_value_callback: It's a function that should return a value
            to initial value, called when the item is created or when cancel
            is called. It is especially useful for items that keep their state
            somewhere else.
        @param choices: Valid when the user needs to select a value from a list.
            It has to be a tuple with ``(value, label)``.
        @param needs_label: If True, the widget will have a label with title as
            the text. Items such as list sets this to False.
        @param needs_space: If ``needs_label`` is False, but the widget still wants 
            to be aligned to the right in the window, set this to True.
        @param enabled: If the widget can be edited by the user.
        @param save_callback: A ``function(item, value)`` called when apply is 
            selected and the value must be saved.
        @param disable_check: When true a checkmark to disable the item is added
        @param disabled_value: A value returned when the item is disabled
        '''
        gobject.GObject.__init__(self)
        
        # These properties should not be changed
        self.container = container
        self.read_only = False
        
        # Properties that take in effect while the configuration is running
        # Access then using their public attributes (as implemented
        # with properties below), such as ``item.enabled = False``
        self.__widget = None
        self.__label = None
        self.__enabled = enabled
        if not choices:
            choices = []
        self.__choices = choices

        # These properties do not need any special processing when changed, 
        # they can probably be directly assigned to another value
        self.config_name = config_name 
        self.config_type = config_type 
        self.save_callback = save_callback 
        self.initial_value = initial_value 
        self.initial_value_callback = initial_value_callback
        self.disabled_value = disabled_value
        
        # These properties takes no effect while the configuration is running,
        # unless the widgets are rebuilt (there are no provisions to make that
        # happen at the moment)
        self.title = title
        self.order = order
        if needs_space is None and title is None:
            needs_space = False
            needs_label = False
        self.needs_label = needs_label
        self.needs_space = needs_space
        self.fill = fill
        self.disable_check = disable_check
    
    def _value_changed(self, *args):
        '''
        Should be called everytime the value changes. Emits the value-changed 
        signal.
        
        This method can be chained into widget signals. It will safely ignore
        any argument passed to it.
        '''
        #if self.is_initial_value():
        #    self.emit('initial-state')
        self.emit('value-changed', self.is_initial_value(), self.value)
        
    def _get_choices_labels(self):
        for value, label in self._get_choices_all():
            yield label
        
    def _get_choices_values(self):
        for value, label in self._get_choices_all():
            yield value
        
    def _get_choices_all(self):
        try:
            for choice in self.choices:
                if isinstance(choice, tuple):
                    if len(choice) != 2:
                        raise ValueError
                    yield choice
                else:
                    yield choice, str(choice)
        except (ValueError, TypeError):
            raise Error("Choices '%s' for '%s' is not valid, it should be a (value, label) list or a list of labels" % (self.choices, self.title))
        
    def _build_choices(self):
        '''
        Implement this when you need to build the choices of a widget.
        '''
        pass
    
    def _clear_choices(self):
        '''
        Implement this to clear the choices on the widget.
        '''
        pass
    
    def _set_choices(self, choices):
        '''
        Should set choices and reassign it's old value.
        
        Subclasses do not need no implement this, they should implement 
        _build_choices and _clear_choices. If they do implement it, they should
        not call this method, unless they know what they are doing.
        '''
        value = self.get_value()
        self.__choices = choices
        self._clear_choices()
        self._build_choices()
        self.set_value(value)

    def set_choices(self, choices):
        '''
        Set the choices and recovers the old state if possible.
        '''
        self._set_choices(choices)
    
    choices = property(lambda self: self.__choices, set_choices)
        
    def _attach(self, table, row, in_section):
        '''
        Attach this item's widget to a table.
        '''
        widget = self.get_widget()
        label = self.get_label()
        row += 1
        table.resize(row, 2)
        align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        if in_section:
            align.set_padding(0, 0, 12, 0)
        #FIXME: This would allow the configurator widget to shrink more then
        # it's original size. It might be useful for PaneConfigurator, but
        # it feels weird. And it screws the size requisition, so it's smaller
        # then it should be.
        #if label:
        #    label.set_ellipsize(pango.ELLIPSIZE_END)
        right_align = label or self.needs_space
        if self.fill:
            yoptions = gtk.FILL | gtk.EXPAND
        else:
            yoptions = 0
        if right_align:
            if label:
                align.add(label)
                table.attach(align, 0, 1, row - 1, row, xoptions = gtk.SHRINK | gtk.FILL, yoptions = 0)
            table.attach(widget, 1, 2, row - 1, row, xoptions = gtk.FILL | gtk.EXPAND, yoptions = yoptions)
        else:
            align.add(widget)
            table.attach(align, 0, 2, row - 1, row, xoptions = gtk.FILL | gtk.EXPAND, yoptions = yoptions)
        return row        

    def _enabled_check_toggled(self, widget):
        self.set_enabled(widget.get_active())
        self.emit('value-changed')

    def get_label(self):
        '''
        Returns the gtk.Label to this item (if needed)
        '''
        if self.needs_label and not self.__label:
            label_text = self.title
            if label_text and not label_text.rstrip().endswith(':'):
                label_text += ':'
            if not self.disable_check:
                self.__label = gtk.Label(label_text)
                self.__label.set_alignment(0.0, 0.5)
            else:
                self.__label = gtk.CheckButton()
                self.__label.set_label(self.title)
                self.__label.set_active(self.__enabled)
                self.__label.connect("toggled", lambda widget: self.set_enabled(widget.get_active()))
        return self.__label
    
    def set_label(self, label):
        '''
        Sets the label widget
        '''
        self.__label = label        
        
    label = property(lambda self: self.get_label(), 
                     lambda self, v: self.set_label(v))

    def get_widget(self):
        '''
        Return the widget, building it as needed.
        '''
        if not self.__widget:
            self._build_widget()
            if not self.__widget:
                raise Error("Widget could not be built")
            self.reset()
        return self.__widget

    def set_widget(self, widget):
        '''
        Sets the widget
        '''
        self.__widget = widget
        
    widget = property(lambda self: self.get_widget(), 
                      lambda self, v: self.set_widget(v))

    def get_value(self):
        '''
        Gets the value from the widget. If the widget does not exist yet
        (the container was not built) the initial_value is returned instead.
        
        This is a public interface method, should not be overriden by 
        descendants. Implement _get_value instead.
        
        Note that this method is expected to be cheap. Take care of not having
        heavy processing in this method. 
        It is called every time the user changes the value.
        '''
        #FIXME: This is a hack to allow the Youtube configuration to work.
        # The way this should be implemented is adding a callback to this function
        # or something similar. But because we already have too much callbacks
        # this way is simpler
        if (not self.enabled) and (self.disabled_value is not None):
            return self.disabled_value
        if not self.__widget:
            return self.initial_value
        return self._get_value()
    
    def set_value(self, value):
        '''
        Sets the value of the widget.
        
        This is a public interface method, should not be overriden by 
        descendants. Implement _set_value instead.
        '''
        #FIXME: We should probably check for exceptions here, to avoid not 
        # showing the configuration dialog because a value was invalid,
        # which could occur with invalid config values.
        # We should probably assign the initial value here in case of an 
        # Exception. In case of another Exception, then it's the module fault,
        # and no exception handling should be done.        
        self.initial_value = value
        if not self.__widget:
            return
        self._set_value(value)

    #Set value as a property
    value = property(get_value, set_value)
    
    def get_config_value(self):
        '''
        Returns a dict suitable to a dataprovider set_configuration.
        
        Returning a dict allows subclasses to provide more then one configuration
        value if needed.
        '''
        if not self.config_name:
            return None
        value = self.get_value()
        try:
            if self.config_type:
                self.config_type(value)
        except:
            log.warning("Value %s could not be translated with %s" % (value, self.config_type))
            #raise TypeError()
        else:
            return {self.config_name: value}      
        
    def is_initial_value(self):
        '''
        Returns True if the current value is the initial value.
        '''
        return self.initial_value == self.value
        
    def _set_enabled(self, enabled):
        self.widget.set_sensitive(enabled)
        if self.label:
            if self.disable_check:
                self.__label.set_active(enabled)
            else:
                self.label.set_sensitive(enabled)
        
    def set_enabled(self, enabled):
        '''
        Set the widget sensibility.
        '''
        self.__enabled = enabled
        if self.__widget:
            self._set_enabled(enabled)
            if self.disabled_value is not None:
                log.critical("Toggling enabled")
                self._value_changed()
    
    enabled = property(lambda self: self.__enabled, lambda self, enabled: self.set_enabled(enabled))
        
    def reset(self):
        '''
        Resets the widget to it's initial value.
        '''
        if self.__widget:
            #self.emit('reset')
            #self.widget.set_sensitive(self.enabled)
            self.set_enabled(self.enabled)
            if self.initial_value_callback:
                self.initial_value = self.initial_value_callback(self)
            self.value = self.initial_value
    
    def save_state(self):
        '''
        Save the current value as the initial value.
        '''
        value = self.get_value()
        self.initial_value = value
        if self.save_callback:
            self.save_callback(self, value)
        
    def apply(self):
        '''
        Seve the current value as the initial value and calls the dataprovider
        to save the current value.
        '''
        self.save_state()
        self.container.apply_config([self])          

class ConfigLabel(ItemBase):
    __item_name__ = 'label'
    
    def __init__(self, xalignment = 0.0, yalignment = 0.5, use_markup = False, **kwargs):
        ItemBase.__init__(self, **kwargs)
        self.xalignment = xalignment #kwargs.get('xalignment', 0.0)
        self.yalignment = yalignment #kwargs.get('yalignment', 0.5)
        self.use_markup = use_markup #kwargs.get('use_markup', False)
        self.read_only = True
    
    def _build_widget(self):
        self.widget = gtk.Label()
        self.widget.set_alignment(self.xalignment, self.yalignment)
        self.widget.set_use_markup(self.use_markup)
    
    def _get_value(self):
        return self.widget.get_text()
    
    def _set_value(self, value):
        if self.use_markup:
            self.widget.set_markup(str(value))
        else:
            self.widget.set_text(str(value))
            
class ConfigButton(ItemBase):
    __item_name__ = 'button'
    
    def __init__(self, *args, **kwargs):
        action = kwargs.pop('action', None)
        self.image = kwargs.pop('image', None)
        ItemBase.__init__(self, *args, **kwargs)
        self.callback = None
        self.needs_space = kwargs.get('needs_space', False)
        self.needs_label = kwargs.get('needs_label', False)
        if action:
            self.initial_value = action
        self.read_only = True
    
    def _button_clicked(self, button_widget):
        if self.callback:
            self.callback(self)
    
    def _build_widget(self):
        self.widget = gtk.Alignment(1.0, 0.5, 0.0, 1.0)
        button_widget = gtk.Button(self.title)
        if self.image:
            button_widget.set_image(gtk.image_new_from_icon_name(self.image, gtk.ICON_SIZE_BUTTON))
        button_widget.connect("clicked", self._button_clicked)
        self.widget.add(button_widget)
        
    def _set_value(self, value):
        if value is not None and not callable(value):
            raise Error("Button callback must be callable (%s is not)" % (value))
        self.callback = value
        
    def _get_value(self):
        return self.callback
    
class ConfigFileButton(ItemBase):
    __item_name__ = 'filebutton'
    
    def __init__(self, *args, **kwargs):
        self.directory = kwargs.pop('directory', False)
        ItemBase.__init__(self, *args, **kwargs)
        self._current_uri = None
    
    def _selection_changed(self, filechooser):
        uri = filechooser.get_uri()
        #if in folder mode, and no directory is selected, then
        #default to the current directory. This hack was necessary in some
        #old pygtk version, I am not sure if it is still required, as the
        #filechooser seems to behave better now
        if self.directory and not uri:
            uri = filechooser.get_current_folder_uri()

        if uri and self._current_uri != uri:
            self._current_uri = uri
            self._value_changed()            
    
    def _build_widget(self):
        self.widget = gtk.FileChooserButton(self.title)
        self.widget.props.local_only = not Vfs.backend_supports_remote_uri_schemes()
        self.widget.connect("selection-changed", self._selection_changed)
        if self.directory:
            self.widget.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        else:
            self.widget.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    
    def _set_value(self, value):
        self.widget.set_uri(str(value))
    
    def _get_value(self):
        return self._current_uri

class ConfigRadio(ItemBase):
    __item_name__ = 'radio'
    
    def __init__(self, container, title, order, **kwargs):
        ItemBase.__init__(self, container, title, order, **kwargs)
        self.needs_label = title is not None
        self.buttons = {}
        self._active_button = None
    
    def _button_changed(self, button):
        if button.get_active():
            self._active_button = button
            self._value_changed()
    
    def _clear_choices(self):
        for widget in self.widget.get_children():
            self.widget.remove(widget)
        self.buttons = {}        
  
    def _build_choices(self):
        last_button = None
        for value, text in self._get_choices_all():
            last_button = gtk.RadioButton(last_button, text)
            last_button.connect("toggled", self._button_changed)
            last_button.show()
            self.buttons[value] = last_button
            self.widget.pack_start(last_button)
    
    def _build_widget(self):
        self.widget = gtk.VBox()
        self._build_choices()
    
    def _get_value(self):
        for value, button in self.buttons.iteritems():
            if button == self._active_button:
                return value
        return None
    
    def _set_value(self, new_value):
        if new_value in self.buttons:
            self.buttons[new_value].set_active(True)
            self._active_button = self.buttons[new_value]
        else:
            log.warn("Value %s could not be applied to config %s" % (new_value, self.title))

class ConfigSpin(ItemBase):
    __item_name__ = 'spin'
    
    def __init__(self, *args, **kwargs):
        self.maximum = kwargs.pop('maximum', sys.maxint)
        self.minimum = kwargs.pop('minimum', 0)
        self.step = kwargs.pop('step', 1)
        ItemBase.__init__(self, *args, **kwargs)
    
    def _build_widget(self):
        self.adjust = gtk.Adjustment(lower = self.minimum, upper = self.maximum, step_incr = self.step)
        self.widget = gtk.SpinButton(self.adjust)
        self.widget.connect("value-changed", self._value_changed)
    
    def _get_value(self):
        return float(self.widget.get_value())
    
    def _set_value(self, value):
        try:
            value = float(value)
            self.widget.set_value(value)
        except:
            log.warn("Value %s could not be applied to config %s" % (repr(self.title), value))        

class ConfigCombo(ItemBase):
    __item_name__ = 'combo'
    
    def _build_choices(self):
        for label in self._get_choices_labels():
            self.widget.append_text(label)
    
    def _clear_choices(self):
        self.widget.get_model().clear()
    
    def _build_widget(self):
        self.widget = gtk.combo_box_new_text()
        self._build_choices()
        self.widget.connect("changed", self._value_changed)

    def _get_value(self):
        active = self.widget.get_active()
        if len(self.choices) > active and active >= 0:
            return [value for value in self._get_choices_values()][active]
        else:
            log.warn("No value selected in combo")
            return None
    
    def _set_value(self, new_value):
        for idx, value in enumerate(self._get_choices_values()):
            if value == new_value:
                self.widget.set_active(idx)
                return
        log.warn("Value %s not found in config %s" % (new_value, self.title))
        
class ConfigComboText(ConfigCombo):
    __item_name__ = 'combotext'

    def _build_widget(self):
        self.widget = gtk.combo_box_entry_new_text()
        self._build_choices()
        self.widget.connect("changed", self._value_changed)
    
    def _get_value(self):
        return self.widget.child.get_text()
    
    def _set_value(self, value):
        self.widget.child.set_text(str(value))
    
class ConfigText(ItemBase):
    __item_name__ = 'text'
    
    def __init__(self, password = False, **kwargs):
        self.password = password #kwargs.pop('password', False)
        ItemBase.__init__(self, **kwargs)
    
    def _build_widget(self):
        self.widget = gtk.Entry()
        self.widget.connect("notify::text", self._value_changed)
        self.widget.set_visibility(not self.password)
    
    def _get_value(self):
        return self.widget.get_text()
    
    def _set_value(self, value):
        self.widget.set_text(str(value))
            
class ConfigList(ItemBase):
    __item_name__ = 'list'
    
    CHECKED_COLUMN, LABEL_COLUMN, VALUE_COLUMN = range(3)
    
    def __init__(self, *args, **kwargs):
        ItemBase.__init__(self, *args, **kwargs)
        self.needs_label = kwargs.get('needs_label', False)
        if self.initial_value:
            try:
                self.initial_value = sorted(self.initial_value)
            except TypeError:
                raise Error("List only supports iterables as value (%s is not)" % (self.initial_value))
        self.fill = kwargs.get('fill', True)
        self._checked_items = None
        self.model = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, object)
    
    def _cellcheck_cb(self, cell, path, model):
        model[path][self.CHECKED_COLUMN] = not cell.get_active()
        #FIXME: Use _checked_items here too, so it's faster to get the values
        #But we should take care that this list must be always sorted
        self._checked_items = None        
        self._value_changed()
    
    def _build_choices(self):
        for value, label in self._get_choices_all():
            self.model.append((False, str(label), value))

    def _clear_choices(self):
        self.model.clear()
    
    def _set_enabled(self, enabled):
        self.list.set_sensitive(enabled)
    
    def _build_widget(self):
        self.vbox = gtk.VBox()
        self.vbox.set_spacing(4)
        self.scrolled_window = gtk.ScrolledWindow()        
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(self.scrolled_window)
        self.total_label = gtk.Label()
        self.total_label.set_alignment(0.0, 0.0)
        self.vbox.pack_start(self.total_label, False, False)
        self.list = gtk.TreeView()        
        self.list.set_property('headers-visible', False)
        self.list.set_property('rules-hint', True)
        self.list.set_model(self.model)        
        check_renderer = gtk.CellRendererToggle()
        check_renderer.set_property('activatable', True)
        check_renderer.connect('toggled', self._cellcheck_cb, self.model)
        #FIXME: We could probably support more columns, maybe by automatically
        # detecting if choices include tuples, and which types are inside the 
        # tuple.
        self.list.append_column(gtk.TreeViewColumn("Enabled", check_renderer, active = self.CHECKED_COLUMN))
        self.list.append_column(gtk.TreeViewColumn("Label", gtk.CellRendererText(), text = self.LABEL_COLUMN))
        self._clear_choices()  
        self._build_choices()
        self.scrolled_window.add(self.list)
        self.widget = self.vbox
        self.widget.set_size_request(-1, 150)
    
    def _update_total(self):
        self.total_label.set_text(_("Total: %d") % len(self._checked_items))
    
    def _get_value(self):
        if not self._checked_items:
            self._checked_items = sorted([row[self.VALUE_COLUMN] for row in self.model if row[self.CHECKED_COLUMN]])
            self._update_total()
        return self._checked_items
    
    def _set_value(self, value):
        self._checked_items = []
        try:
            self._checked_items = sorted(value)
            for row in self.model:
                row[self.CHECKED_COLUMN] = (row[self.VALUE_COLUMN] in self._checked_items)
        except:
            log.warn("Value %s could not be added to list %s" % (value, repr(self.title)))
        self._update_total()

class ConfigCheckBox(ItemBase):
    __item_name__ = 'check'
    
    def __init__(self, *args, **kwargs):
        ItemBase.__init__(self, *args, **kwargs)
        self.needs_label = False
        
    def _build_widget(self):
        self.widget = gtk.CheckButton()
        self.widget.set_label(self.title)
        self.widget.connect("toggled", self._value_changed)
    
    def _get_value(self):
        return self.widget.get_active()
    
    def _set_value(self, value):
        self.widget.set_active(bool(value))


