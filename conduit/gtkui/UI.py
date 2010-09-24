"""
Draws the applications main window

Also manages the callbacks from menu and GUI items

Copyright: John Stowers, 2006
License: GPLv2
"""
import thread
import gobject
import gtk
import os.path
import gettext
import threading
from gettext import gettext as _
import logging
log = logging.getLogger("gtkui.UI")

import conduit
import conduit.Web as Web
import conduit.Conduit as Conduit
import conduit.utils.AutostartManager as AutostartManager
import conduit.gtkui.Canvas as Canvas
import conduit.gtkui.MsgArea as MsgArea
import conduit.gtkui.Tree as Tree
import conduit.gtkui.ConflictResolver as ConflictResolver
import conduit.gtkui.Database as Database

def N_(message): return message

DEVELOPER_WEB_LINKS = (
#name,                      #url
(N_("Introduction"),            "http://www.conduit-project.org/wiki/Development"),
(N_("Writing a Data Provider"), "http://www.conduit-project.org/wiki/WritingADataProvider"),
(N_("API Documentation"),       "http://doc.conduit-project.org/conduit/"),
(N_("Test Results"),            "http://tests.conduit-project.org/")
)

#set up the gettext system and locales
for module in (gettext,):
    module.bindtextdomain('conduit', conduit.LOCALE_DIR)
    module.textdomain('conduit')
    if hasattr(module, 'bind_textdomain_codeset'):
        module.bind_textdomain_codeset('conduit','UTF-8')

class _PreconfiguredConduitMenu:
    """
    Manages the list of preconfigured conduits examples
    """
    def __init__(self):
        self.menu = gtk.Menu()
        self.item = gtk.ImageMenuItem(_("Examples"))
        self.item.set_image(
                gtk.image_new_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU))
        self.item.set_submenu(self.menu)

        #FIXME: Add remove items when dps become availalbe
        # self._items = {}
        # conduit.GLOBALS.moduleManager.connect("dataprovider-available", self._dp_added)
        # conduit.GLOBALS.moduleManager.connect("dataprovider-unavailable", self._dp_removed)

        preconfigured = conduit.GLOBALS.moduleManager.list_preconfigured_conduits()
        if preconfigured:
            for sok,sik,desc,w in preconfigured:
                item = gtk.MenuItem(desc)
                item.connect("activate", self._create, sok, sik, w)
                item.show()
                self.menu.append(item)
        else:
            self.item.set_sensitive(False)

    def _create(self, menu, sok, sik, w):
        self.syncSet.create_preconfigured_conduit(sok,sik,w)
        
    def _dp_added(self, manager, dpw):
        item = gtk.MenuItem(dpw.get_key())
        self._items[dpw] = item
        self.menu.append(item)
        item.show()
        
    def _dp_removed(self, manager, dpw):
        self.menu.remove(self._items[dpw])

    def set_sync_set(self, syncSet):
        self.syncSet = syncSet

class _GtkBuilderWrapper(gtk.Builder):
    def __init__(self, *path):
        gtk.Builder.__init__(self)
        self.add_from_file(os.path.join(*path))
        self._resources = {}

    def set_instance_resources(self, obj, *resources):
        for r in resources:
            setattr(obj, "_%s" % r.lower(), self.get_resource(r))

    def get_object(self, name):
        if name not in self._resources:
            w = gtk.Builder.get_object(self,name)
            if not w:
                raise Exception("Could not find widget: %s" % name)
            self._resources[name] = w

        return self._resources[name]

    def connect_signals(self, obj):
        #FIXME: connect_signals seems to be only able to be called once
        missing = gtk.Builder.connect_signals(self, obj)
        if missing:
            log.critical("Failed to connect signals: %s" % ",".join(missing))

class PreferencesWindow:

    NOTEBOOK_FIXED_PAGES = 3

    def __init__(self, gtkbuilder):
        self._gtkbuilder = gtkbuilder
        self._extra_pages = []
        self._notebook = self._gtkbuilder.get_object("prop_notebook")
        self._autostartmanager = AutostartManager.AutostartManager()

    def _add_page(self, widget, label):
        self._notebook.append_page(widget,label)
        self._extra_pages.append(widget)

    def _remove_extra_pages(self):
        for w in self._extra_pages:
            pn = self._notebook.page_num(w)
            if pn >= self.NOTEBOOK_FIXED_PAGES:
                self._notebook.remove_page( pn )

    def show(self, parent):
        def on_clear_button_clicked(sender, treeview, sqliteListStore):
            treeview.set_model(None)
            conduit.GLOBALS.mappingDB.delete()
            treeview.set_model(sqliteListStore)

        #Build some liststores to display
        CONVERT_FROM_MESSAGE = _("Convert from")
        CONVERT_INTO_MESSAGE = _("into")

        #reset the prefs window, removing all dynamically added pages
        self._remove_extra_pages()

        convertables = conduit.GLOBALS.typeConverter.get_convertables_list()
        converterListStore = gtk.ListStore( str )
        for froms,tos in convertables:
            string = "%s %s %s %s" % (CONVERT_FROM_MESSAGE, froms, CONVERT_INTO_MESSAGE, tos)
            converterListStore.append( (string,) )
        dataProviderListStore = gtk.ListStore( str, bool )
        #get all dataproviders
        for i in conduit.GLOBALS.moduleManager.get_modules_by_type("sink","source","twoway"):
            dataProviderListStore.append(("Name: %s\nDescription: %s)" % (i.name, i.description), True))
        #include files that could not be loaded
        for f in conduit.GLOBALS.moduleManager.invalidFiles:
            dataProviderListStore.append(("Error loading file: %s" % f, False))

        #Show the DB contents to help debugging
        if conduit.IS_DEVELOPMENT_VERSION:
            vbox = gtk.VBox(False,5)
            
            #build the treeview to show all column fields. For performance
            #reasons it is fixed_height and fixed_FIXE
            treeview = gtk.TreeView()
            treeview.set_headers_visible(True)
            treeview.set_fixed_height_mode(True)
            index = 1
            db = conduit.GLOBALS.mappingDB._db
            for name in db.get_fields("mappings"):
                column = gtk.TreeViewColumn(
                                    name, 
                                    gtk.CellRendererText(),
                                    text=index)
                column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                column.set_fixed_width(250)
                treeview.append_column(column)
                index = index + 1

            store = Database.GenericDBListStore("mappings", db)
            treeview.set_model(store)            
            
            sw = gtk.ScrolledWindow()
            sw.add(treeview)
            vbox.pack_start(sw,True,True)

            clear = gtk.Button(None,gtk.STOCK_CLEAR)
            clear.connect("clicked", on_clear_button_clicked, treeview, store)
            vbox.pack_start(clear, False, False)

            self._add_page(vbox,gtk.Label(_('Relationship Database')))
        
        converterTreeView = self._gtkbuilder.get_object("dataConversionsTreeView")
        converterTreeView.set_model(converterListStore)
        converterTreeView.append_column(gtk.TreeViewColumn(_("Conversions Available"), 
                                        gtk.CellRendererText(), 
                                        text=0)
                                        )
        dataproviderTreeView = self._gtkbuilder.get_object("dataProvidersTreeView")
        dataproviderTreeView.set_model(dataProviderListStore)
        dataproviderTreeView.append_column(gtk.TreeViewColumn(_("Name"), 
                                        gtk.CellRendererText(), 
                                        text=0)
                                        )                                                   
        dataproviderTreeView.append_column(gtk.TreeViewColumn(_("Loaded"), 
                                        gtk.CellRendererToggle(), 
                                        active=1)
                                        )                                        
                                        
        #fill out the configuration tab
        save_settings_check = self._gtkbuilder.get_object("save_settings_check")
        save_settings_check.set_active(conduit.GLOBALS.settings.get("save_on_exit"))
        status_icon_check = self._gtkbuilder.get_object("status_icon_check")
        status_icon_check.set_active(conduit.GLOBALS.settings.get("show_status_icon")) 
        minimize_to_tray_check = self._gtkbuilder.get_object("minimize_to_tray_check")
        minimize_to_tray_check.set_active(conduit.GLOBALS.settings.get("gui_minimize_to_tray")) 
        show_hints_check = self._gtkbuilder.get_object("show_hints_check")
        show_hints_check.set_active(conduit.GLOBALS.settings.get("gui_show_hints"))

        #special case start at login. Because we copy the desktop file from the
        #system to ~/.config/autostart, we require conduit to be installed
        start_at_login_check = self._gtkbuilder.get_object("start_at_login")
        if conduit.IS_INSTALLED:
            start_at_login_check.set_active(self._autostartmanager.is_start_at_login_enabled())
        else:
            start_at_login_check.set_sensitive(False)

        #restore the current policy
        for policyName in Conduit.CONFLICT_POLICY_NAMES:
            currentValue = conduit.GLOBALS.settings.get("default_policy_%s" % policyName)
            for policyValue in Conduit.CONFLICT_POLICY_VALUES:
                name = "%s_%s" % (policyName,policyValue)
                widget = self._gtkbuilder.get_object(name+"_radio")
                widget.set_image(
                        gtk.image_new_from_icon_name(
                                Conduit.CONFLICT_POLICY_VALUE_ICONS[name],
                                gtk.ICON_SIZE_MENU))
                if currentValue == policyValue:
                    widget.set_active(True)

        #The dataprovider factories can provide a configuration widget which is
        #packed into the notebook
        for i in conduit.GLOBALS.moduleManager.dataproviderFactories:#get_modules_by_type("dataprovider-factory"):
            widget = i.setup_configuration_widget()
            if widget:
                self._add_page(
                            widget,
                            gtk.Label(i.get_name()))

        #Show the dialog
        dialog = self._gtkbuilder.get_object("PreferencesDialog")
        dialog.show_all()
        dialog.set_transient_for(parent)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            conduit.GLOBALS.settings.set("save_on_exit", save_settings_check.get_active())
            conduit.GLOBALS.settings.set("show_status_icon", status_icon_check.get_active())
            conduit.GLOBALS.settings.set("gui_minimize_to_tray", minimize_to_tray_check.get_active())
            conduit.GLOBALS.settings.set("gui_show_hints", show_hints_check.get_active())
            self._autostartmanager.update_start_at_login(start_at_login_check.get_active())
            #save the current policy
            for policyName in Conduit.CONFLICT_POLICY_NAMES:
                for policyValue in Conduit.CONFLICT_POLICY_VALUES:
                    name = "%s_%s" % (policyName,policyValue)
                    if self._gtkbuilder.get_object(name+"_radio").get_active() == True:
                        conduit.GLOBALS.settings.set(
                                "default_policy_%s" % policyName,
                                policyValue)

        #give the dataprovider factories to ability to save themselves
        for factory in conduit.GLOBALS.moduleManager.dataproviderFactories:
            factory.save_configuration(response == gtk.RESPONSE_OK)

        dialog.hide()                

class MainWindow:
    """
    The main conduit window.
    """
    def __init__(self, conduitApplication, moduleManager, typeConverter, syncManager):
        """
        Constructs the mainwindow. Throws up a splash screen to cover 
        the most time consuming pieces
        """
        #add some additional dirs to the icon theme search path so that
        #modules can provider their own icons
        icon_dirs = [
                    conduit.SHARED_DATA_DIR,
                    conduit.SHARED_MODULE_DIR,
                    os.path.join(conduit.SHARED_DATA_DIR,"icons"),
                    os.path.join(conduit.USER_DIR, "modules")
                    ]
        for i in icon_dirs:                    
            gtk.icon_theme_get_default().prepend_search_path(i)
        gtk.window_set_default_icon_name("conduit")

        signals = { 
                "on_mainwindow_delete" : self.on_window_closed,
                "on_mainwindow_state_event" : self.on_window_state_event,
                "on_synchronize_activate" : self.on_synchronize_all_clicked,
                "on_cancel_activate" : self.on_cancel_all_clicked,  
                "on_quit_activate" : self.on_window_closed,
                "on_clear_canvas_activate" : self.on_clear_canvas,
                "on_preferences_activate" : self.on_conduit_preferences,
                "on_about_activate" : self.on_about_conduit,
                "on_contents_activate" : self.on_help,
                "on_save1_activate" : self.save_settings,
                }

        self.conduitApplication = conduitApplication
        self.builder = _GtkBuilderWrapper(conduit.SHARED_DATA_DIR, "conduit.ui")
        self.builder.connect_signals(signals)

        #type converter and sync manager
        self.type_converter = typeConverter
        self.sync_manager = syncManager
        
        #Initialize the mainWindow
        self.mainWindow = self.builder.get_object("MainWindow")
        #Enable RGBA colormap
        if conduit.GLOBALS.settings.get("gui_use_rgba_colormap") == True:
            screen = self.mainWindow.get_screen()
            colormap = screen.get_rgba_colormap()
            if colormap:
                gtk.widget_set_default_colormap(colormap)
        self.mainWindow.set_position(gtk.WIN_POS_CENTER)
        title = "Conduit"
        if conduit.IS_DEVELOPMENT_VERSION:
            title = title + _(" - %s (Development Version)") % conduit.VERSION
        if not conduit.IS_INSTALLED:
            title = title + _(" - Running Uninstalled")
        self.mainWindow.set_title(title)

        #Configure canvas
        self.canvasSW = self.builder.get_object("canvasScrolledWindow")
        self.hpane = self.builder.get_object("hpaned1")

        #start up the canvas
        msg = MsgArea.MsgAreaController()
        self.builder.get_object("mainVbox").pack_start(msg, False, False)
        self.canvas = Canvas.Canvas(
                        parentWindow=self.mainWindow,
                        typeConverter=self.type_converter,
                        syncManager=self.sync_manager,
                        gtkbuilder=self.builder,
                        msg=msg
                        )
        self.canvasSW.add(self.canvas)
        self.canvas.connect('drag-drop', self.drop_cb)
        self.canvas.connect("drag-data-received", self.drag_data_received_data)
        
        # Populate the tree model
        self.dataproviderTreeModel = Tree.DataProviderTreeModel() 
        dataproviderScrolledWindow = self.builder.get_object("scrolledwindow2")
        self.dataproviderTreeView = Tree.DataProviderTreeView(self.dataproviderTreeModel)
        dataproviderScrolledWindow.add(self.dataproviderTreeView)

        #Set up the expander used for resolving sync conflicts
        self.conflictResolver = ConflictResolver.ConflictResolver(self.builder)

        #Preferences manager
        self.preferences = PreferencesWindow(self.builder)
        
        #add the preconfigured Conduit menu
        if conduit.GLOBALS.settings.get("gui_show_hints"):
            self.preconfiguredConduitsMenu = _PreconfiguredConduitMenu()
            self.builder.get_object("file_menu").insert(self.preconfiguredConduitsMenu.item, 3)
        else:
            self.preconfiguredConduitsMenu = None

        #if running a development version, add some developer specific links
        #to the help menu
        if conduit.IS_DEVELOPMENT_VERSION:
            helpMenu = self.builder.get_object("help_menu")
            developersMenuItem = gtk.ImageMenuItem(_("Developers"))
            developersMenuItem.set_image(
                                gtk.image_new_from_icon_name(
                                        "applications-development",
                                        gtk.ICON_SIZE_MENU))
            developersMenu = gtk.Menu()
            developersMenuItem.set_submenu(developersMenu)
            helpMenu.prepend(developersMenuItem)
            for name,url in DEVELOPER_WEB_LINKS:
                item = gtk.ImageMenuItem(_(name))
                item.set_image(
                        gtk.image_new_from_icon_name(
                                "applications-internet",
                                gtk.ICON_SIZE_MENU))
                item.connect("activate",self.on_developer_menu_item_clicked,_(name),url)
                developersMenu.append(item)

        #final GUI setup
        self.cancelSyncButton = self.builder.get_object('cancel')
        self.hpane.set_position(conduit.GLOBALS.settings.get("gui_hpane_postion"))
        self.dataproviderTreeView.set_expand_rows()
        self.window_state = 0                
        log.info("Main window constructed  (thread: %s)" % thread.get_ident())

    def _ui_get_resource(self, name):
        if name not in self.builder_resources:
            w = self.builder.get_object(name)
            if not w:
                raise Exception("Could not find widget: %s" % name)
            self.builder_resources[name] = w

        return self.builder_resources[name]
                
    def on_developer_menu_item_clicked(self, menuitem, name, url):
        threading.Thread(
                    target=Web.LoginMagic,
                    args=(name, url),
                    kwargs={"login_function":lambda: True}
                    ).start()
        
    def on_conduit_added(self, syncset, cond):
        cond.connect("sync-started", self.on_sync_started)
        cond.connect("sync-completed", self.on_sync_completed)
        cond.connect("sync-conflict", self.conflictResolver.on_conflict)

    def set_model(self, syncSet):
        self.syncSet = syncSet
        self.syncSet.connect("conduit-added", self.on_conduit_added)
        self.canvas.set_sync_set(syncSet)
        if self.preconfiguredConduitsMenu:
            self.preconfiguredConduitsMenu.set_sync_set(syncSet)

    def present(self):
        """
        Present the main window. Enjoy your window
        """
        log.debug("Presenting GUI")
        self.mainWindow.show_all()
        self.mainWindow.present()
        
    def minimize_to_tray(self):
        """
        Iconifies the main window
        """
        log.debug("Iconifying GUI")
        self.mainWindow.hide()

    def is_visible(self):
        """
        Returns True if mainWindow is visible
        (not minimized or withdrawn)
        """
        minimized = self.window_state & gtk.gdk.WINDOW_STATE_ICONIFIED
        return (not minimized) and self.mainWindow.get_property('visible')

    def on_sync_started(self, thread):
        self.cancelSyncButton.set_property("sensitive", True)

    def on_sync_completed(self, thread, aborted, error, conflict):
        self.cancelSyncButton.set_property(
                "sensitive",
                conduit.GLOBALS.syncManager.is_busy()
                )
       
    def on_synchronize_all_clicked(self, widget):
        """
        Synchronize all valid conduits on the canvas
        """
        self.conduitApplication.Synchronize()
                
    def on_cancel_all_clicked(self, widget):
        """
        Cancels all currently runnings syncs
        """
        self.conduitApplication.Cancel()

    def on_clear_canvas(self, widget):
        """
        Clear the canvas and start a new sync set
        """
        self.canvas.clear_canvas()
    
    def on_conduit_preferences(self, widget):
        """
        Show the properties of the current sync set (status, conflicts, etc
        Edit the sync specific properties
        """
        self.preferences.show(self.mainWindow)

    def on_about_conduit(self, widget):
        """
        Display about dialog
        """
        dialog = AboutDialog()
        dialog.set_transient_for(self.mainWindow)
        dialog.run()
        dialog.destroy()
        
    def on_help(self, widget):
        """
        Display help
        """
        if conduit.IS_INSTALLED:
            uri = "ghelp:conduit"
        else:
            #if we are not installed then launch the ghelp uri with a full path
            uri = "ghelp:%s" % os.path.join(conduit.DIRECTORY,"help","C","conduit.xml")

        log.debug("Launching help: %s" % uri)

        gtk.show_uri(
            self.mainWindow.get_screen(),
            uri,
            gtk.get_current_event_time())

    def on_window_state_event(self, widget, event):
        visible = self.is_visible()
        self.window_state = event.new_window_state
        if self.window_state & gtk.gdk.WINDOW_STATE_ICONIFIED and visible:
            if conduit.GLOBALS.settings.get("gui_minimize_to_tray"):
                self.minimize_to_tray()

    def on_window_closed(self, widget, event=None):
        """
        Check if there are any synchronizations currently in progress and
        ask the user if they wish to cancel them
        """
        busy = False
        quit = False
        for c in self.syncSet.get_all_conduits(): 
            if c.is_busy():
                busy = True
               
        if busy:       
            dialog = gtk.MessageDialog(
                            self.mainWindow,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_QUESTION,
                            gtk.BUTTONS_YES_NO,_("Synchronization in progress. Do you want to cancel it?")
                            )
            response = dialog.run()
            if response == gtk.RESPONSE_YES:
                quit = True
            else:
                #Dont exit
                dialog.destroy()
                return True
        else:
            quit = True
            
        #OK, if we have decided to quit then call quit on the 
        #DBus interface which will tidy up any pending running
        #non gui tasks
        if quit:
            self.conduitApplication.Quit()
        
        
    def drop_cb(self, wid, context, x, y, time):
        """
        drop cb
        """
        if context.targets:
            target = context.targets[0]
        else:
            # FIXME: work-around for a bug in PyGTK on OSX: 
            # http://bugzilla.gnome.org/show_bug.cgi?id=588643
            target = 'conduit/element-name'
        self.canvas.drag_get_data(context, target, time)
        return True
        
    def drag_data_received_data(self, treeview, context, x, y, selection, info, etime):
        """
        DND
        """
        dataproviderKey = selection.data
        #FIXME: DnD should be cancelled in the Treeview on the drag-begin 
        #signal and NOT here
        if dataproviderKey != "":
            #adjust for scrolled window offset
            scroll = self.canvasSW.get_vadjustment().get_value()

            #Add a new instance if the dataprovider to the canvas.
            new = conduit.GLOBALS.moduleManager.get_module_wrapper_with_instance(dataproviderKey)
            self.canvas.add_dataprovider_to_canvas(
                                dataproviderKey,
                                new,
                                x,
                                int(scroll) + y
                                )
        
        context.finish(True, True, etime)
        return
        
    def save_settings(self, widget):
        """
        Saves the application settings to an XML document.
        Saves the GUI settings (window state, position, etc to gconf)
        """
        #save the canvas
        self.syncSet.save_to_xml()

        #GUI settings
        conduit.GLOBALS.settings.set(
                            "gui_hpane_postion",
                            self.hpane.get_position())
        conduit.GLOBALS.settings.set(
                            "gui_window_size",
                            self.mainWindow.get_size())
        conduit.GLOBALS.settings.set(
                            "gui_expanded_rows",
                            self.dataproviderTreeView.get_expanded_rows())

class SplashScreen:
    """
    Simple splash screen class which shows an image for a predetermined period
    of time or until L{SplashScreen.destroy} is called.
    
    Code adapted from banshee
    """
    DELAY = 1500 #msec
    def __init__(self):        
        """
        Constructor
        """
        #If false the main window should call destroy() to remove the splash
        self.destroyed = True
        
    def show(self):
        """
        Builds the splashscreen and connects the splash window to be destroyed 
        via a timeout callback in L{SplashScreen.DELAY}msec time.

        The splash can also be destroyed manually by the application
        """
        self.wSplash = gtk.Window(gtk.WINDOW_POPUP)
        self.wSplash.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)
        self.wSplash.set_decorated(False)

        wSplashScreen = gtk.Image()
        wSplashScreen.set_from_file(os.path.join(conduit.SHARED_DATA_DIR,"conduit-splash.png"))

        # Make a pretty frame
        wSplashFrame = gtk.Frame()
        wSplashFrame.set_shadow_type(gtk.SHADOW_OUT)
        wSplashFrame.add(wSplashScreen)
        self.wSplash.add(wSplashFrame)

        # OK throw up the splashscreen
        self.wSplash.set_position(gtk.WIN_POS_CENTER)
        
        #The splash screen is destroyed automatically (via timeout)
        #or when the application is finished loading
        self.destroyed = False

        self.wSplash.show_all()
        # ensure it is rendered immediately
        while gtk.events_pending():
            gtk.main_iteration() 
        # The idle timeout handler to destroy the splashscreen
        gobject.timeout_add(SplashScreen.DELAY,self.destroy)

    def destroy(self):
        """
        Destroys the splashscreen. Can be safely called manually (prior to) 
        or via the timer callback
        """
        if not self.destroyed:
            self.wSplash.destroy()
            self.destroyed = True

class AboutDialog(gtk.AboutDialog):
    def __init__(self):
        gtk.AboutDialog.__init__(self)
        self.set_name("Conduit")
        self.set_version(conduit.VERSION)
        self.set_comments("Synchronisation for GNOME")
        self.set_website("http://www.conduit-project.org")
        self.set_authors([
        		"John Stowers",
        		"John Carr",
        		"Thomas Van Machelen",
        		"Jonny Lamb",
                "Alexandre Rosenfeld",
                "Andrew Stormont"])
        self.set_artists([
        		"John Stowers",
        		"mejogid",
        		"The Tango Project (http://tango.freedesktop.org)"])
        self.set_logo_icon_name("conduit")

class StatusIcon(gtk.StatusIcon):
    def __init__(self, conduitApplication):
        gtk.StatusIcon.__init__(self)

        #we need some custom icons
        gtk.icon_theme_get_default().prepend_search_path(conduit.SHARED_DATA_DIR)

        self.conduitApplication = conduitApplication
        menu = '''
            <ui>
             <menubar name="Menubar">
              <menu action="Menu">
               <menuitem action="Sync"/>
               <menuitem action="Cancel"/>
               <menuitem action="Quit"/>
              </menu>
             </menubar>
            </ui>
        '''
        actions = [
            ('Menu',  None, 'Menu'),
            ('Sync', gtk.STOCK_EXECUTE, _("_Synchronize All"), None, _("Synchronizes All Groups"), self.on_synchronize),
            ('Cancel', gtk.STOCK_CANCEL, _("_Cancel Synchronization"), None, _("Cancels Currently Synchronizing Groups"), self.on_cancel),
            ('Quit', gtk.STOCK_QUIT, _("_Quit"), None, _("Close Conduit"), self.on_quit)]
        ag = gtk.ActionGroup('Actions')
        ag.add_actions(actions)
        self.manager = gtk.UIManager()
        self.manager.insert_action_group(ag, 0)
        self.manager.add_ui_from_string(menu)
        self.menu = self.manager.get_widget('/Menubar/Menu/Quit').props.parent
        self.cancelButton = self.manager.get_widget('/Menubar/Menu/Cancel')   
        self.connect('popup-menu', self.on_popup_menu)
        self.connect('activate', self.on_click)

        self.cancelButton.set_property("sensitive", False)
        self.set_from_icon_name("conduit")
        self.set_tooltip("Conduit")
        self.set_visible(True)

    def _on_sync_started(self, cond):
        self.set_tooltip(_("Synchronizing"))
        self.cancelButton.set_property("sensitive", True)

    def _on_sync_completed(self, cond, aborted, error, conflict):
        if not aborted and not error and not conflict:
            self.set_from_icon_name("conduit")
            self.set_tooltip(_("Synchronization Complete"))
        else:
            self.set_from_icon_name("dialog-error")
            if aborted or error:
                self.set_tooltip(_("Synchronization Error"))
            else:
                self.set_tooltip(_("Synchronization Conflict"))
        self.cancelButton.set_property("sensitive", False)

    def on_conduit_added(self, syncset, cond):
        cond.connect("sync-started", self._on_sync_started)
        cond.connect("sync-completed", self._on_sync_completed)

    def on_conduit_removed(self, syncset, cond):
        pass

    def on_synchronize(self, data):
        self.conduitApplication.Synchronize()
        
    def on_cancel(self, data):
        self.conduitApplication.Cancel()

    def on_popup_menu(self, status, button, time):
        self.menu.popup(None, None, gtk.status_icon_position_menu, button, time, data=status)

    def on_quit(self, data):
        self.conduitApplication.Quit()

    def on_click(self, status):
        if self.conduitApplication.HasGUI():
            if self.conduitApplication.gui.is_visible():
                self.conduitApplication.gui.minimize_to_tray()
            else:
                self.conduitApplication.gui.present()
        else:
            self.conduitApplication.BuildGUI()
            self.conduitApplication.ShowGUI()

def main_loop():
    gtk.main()

def main_quit():
    gtk.main_quit()

