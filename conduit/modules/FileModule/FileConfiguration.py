import gobject
import gtk
from gettext import gettext as _
import logging
log = logging.getLogger("modules.File")

import conduit
import conduit.vfs as Vfs
import conduit.vfs.File as VfsFile
import conduit.gtkui.Database as Database
import conduit.dataproviders.File as FileDataProvider
import conduit.Configurator as Configurator

#Indexes of data in the list store
OID_IDX = 0
URI_IDX = 1                     #URI of the file/folder
TYPE_IDX = 2                    #TYPE_FILE/FOLDER/etc
CONTAINS_NUM_ITEMS_IDX = 3      #(folder only) How many items in the folder
SCAN_COMPLETE_IDX = 4           #(folder only) HAs the folder been recursively scanned
GROUP_NAME_IDX = 5              #(folder only) The visible identifier for the folder

class _FileSourceConfigurator(VfsFile.FolderScannerThreadManager, Configurator.BaseConfigContainer):
    """
    Configuration dialog for the FileTwoway dataprovider
    """
    try:
        FILE_ICON = gtk.icon_theme_get_default().load_icon("text-x-generic", 16, 0)
        FOLDER_ICON = gtk.icon_theme_get_default().load_icon("folder", 16, 0)
    except:
        # FIXME: icon handling should be done better on Maemo
        pass        

    def __init__(self, dataprovider, configurator, db):
        VfsFile.FolderScannerThreadManager.__init__(self)
        Configurator.BaseConfigContainer.__init__(self, dataprovider, configurator)
        self.db = db
        self.tree_model = Database.GenericDBListStore("config", self.db)

        self._make_ui()

        #Now go an background scan some folders to populate the UI estimates.
        for oid,uri in self.db.select("SELECT oid,URI FROM config WHERE TYPE=? and SCAN_COMPLETE=?",(FileDataProvider.TYPE_FOLDER,False,)):
            self.make_thread(
                    uri,
                    False,  #include hidden
                    False,  #follow symlinks
                    self._on_scan_folder_progress,
                    self._on_scan_folder_completed,
                    oid
                    )

    def _dnd_data_get(self, wid, context, x, y, selection, targetType, time):
        for uri in selection.get_uris():
            try:
                log.debug("Drag recieved %s" % uri)
                if Vfs.uri_is_folder(uri):
                    self._add_folder(uri)
                else:
                    self._add_file(uri)
            except Exception, err:
                log.debug("Error adding %s\n%s" % (uri,err))

    def _make_ui(self):
        """
        Creates the ui
        """
        self.frame = gtk.Frame("Files and Folders to Synchronize")
        self.frame.props.shadow_type = gtk.SHADOW_NONE

        align = gtk.Alignment(0.5,0.5,1.0,1.0)
        align.props.left_padding = 12
        self.frame.add(align)

        sw = gtk.ScrolledWindow()
        sw.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC 
        sw.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC 
        sw.props.shadow_type= gtk.SHADOW_IN
        #setup dnd onto the file list
        sw.drag_dest_set(
            gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
            [ ( "text/uri-list", 0, 0 ) ],
            gtk.gdk.ACTION_COPY
            )
        sw.connect("drag_data_received", self._dnd_data_get)

        af = gtk.Button("_Add File")
        af.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
        af.connect("clicked", self.on_addfile_clicked)
        ad = gtk.Button("Add _Directory")
        ad.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
        ad.connect("clicked", self.on_adddir_clicked)
        r = gtk.Button(stock=gtk.STOCK_REMOVE)
        r.connect("clicked", self.on_remove_clicked)

        hbb = gtk.HButtonBox()
        hbb.props.layout_style = gtk.BUTTONBOX_SPREAD
        hbb.props.spacing = 3
        hbb.add(af)
        hbb.add(ad)
        hbb.add(r)

        vb = gtk.VBox()
        vb.pack_start(sw, expand=True, fill=True)
        vb.pack_end(hbb, expand=False, fill=True, padding=5)
        align.add(vb)

        self.view = gtk.TreeView(self.tree_model)
        sw.add(self.view)

        #First column is an icon (folder of File)
        iconRenderer = gtk.CellRendererPixbuf()
        column1 = gtk.TreeViewColumn(_("Icon"), iconRenderer)
        column1.set_cell_data_func(iconRenderer, self._item_icon_data_func)
        self.view.append_column(column1)
        #Second column is the File/Folder name
        nameRenderer = gtk.CellRendererText()
        nameRenderer.connect('edited', self._item_name_edited_callback)
        column2 = gtk.TreeViewColumn(_("Name"), nameRenderer)
        column2.set_property("expand", True)
        column2.set_cell_data_func(nameRenderer, self._item_name_data_func)
        self.view.append_column(column2)
        #Third column is the number of contained items
        containsNumRenderer = gtk.CellRendererText()
        column3 = gtk.TreeViewColumn(_("Items"), containsNumRenderer)
        column3.set_cell_data_func(containsNumRenderer, self._item_contains_num_data_func)
        self.view.append_column(column3)

    def _item_icon_data_func(self, column, cell_renderer, tree_model, rowref):
        """
        Draw the appropriate icon depending if the URI is a
        folder or a file. We only show single files in the GUI anyway
        """
        path = self.tree_model.get_path(rowref)

        if self.tree_model[path][TYPE_IDX] == FileDataProvider.TYPE_FILE:
            icon = _FileSourceConfigurator.FILE_ICON
        else:
            icon = _FileSourceConfigurator.FOLDER_ICON
        cell_renderer.set_property("pixbuf",icon)

    def _item_contains_num_data_func(self, column, cell_renderer, tree_model, rowref):
        """
        Displays the number of files contained within a folder or an empty
        string if the tree_model item is a File
        """
        path = self.tree_model.get_path(rowref)
        if self.tree_model[path][TYPE_IDX] == FileDataProvider.TYPE_FILE:
            contains = ""
        else:
            contains = _("<i>Contains %s files</i>") % self.tree_model[path][CONTAINS_NUM_ITEMS_IDX]
        cell_renderer.set_property("markup",contains)

    def _item_name_data_func(self, column, cell_renderer, tree_model, rowref):
        """
        If the user has set a descriptive name for the folder the display that,
        otherwise display the filename.
        """
        path = self.tree_model.get_path(rowref)
        uri = self.tree_model[path][URI_IDX]

        if self.tree_model[path][GROUP_NAME_IDX] != "":
            displayName = self.tree_model[path][GROUP_NAME_IDX]
        else:
            displayName = Vfs.uri_format_for_display(uri)

        cell_renderer.set_property("text", displayName)
        cell_renderer.set_property("ellipsize", True)

        #Can not edit the group name of a file
        if self.tree_model[path][TYPE_IDX] == FileDataProvider.TYPE_FILE:
            cell_renderer.set_property("editable", False)
        else:
            cell_renderer.set_property("editable", True)

    def _item_name_edited_callback(self, cellrenderertext, path, new_text):
        """
        Called when the user edits the descriptive name of the folder
        """
        self.db.update(
            table="config",
            oid=self.tree_model[path][OID_IDX],
            GROUP_NAME=new_text
            )

    def _on_scan_folder_progress(self, folderScanner, numItems, oid):
        """
        Called by the folder scanner thread and used to update
        the estimate of the number of items in the directory
        """
        self.db.update(
            table="config",
            oid=oid,
            CONTAINS_NUM_ITEMS=numItems
            )

    def _on_scan_folder_completed(self, folderScanner, oid):
        """
        Called when the folder scanner thread completes
        """
        log.debug("Folder scan complete")
        self.db.update(
            table="config",
            oid=oid,
            SCAN_COMPLETE=True
            )

    def _add_folder(self, folderURI):
        """
        Adds the folder to the db. Starts a thread to scan it in the background
        """
        if folderURI not in self.scanThreads:
            name = Vfs.uri_get_filename(folderURI)
            oid = self.db.insert(
                        table="config",
                        values=(folderURI,FileDataProvider.TYPE_FOLDER,0,False,name)
                        )
            self.make_thread(
                    folderURI,
                    False,  #include hidden
                    False,  #follow symlinks
                    self._on_scan_folder_progress,
                    self._on_scan_folder_completed,
                    oid
                    )

    def _add_file(self, uri):
        self.db.insert(
                    table="config",
                    values=(uri,FileDataProvider.TYPE_FILE,0,False,"")
                    )

    def show_dialog(self):
        #response = self.dlg.run()
        #We can actually go ahead and cancel all the threads. The items count
        #is only used as GUI bling and is recalculated in refresh() anyway
        #self.cancel_all_threads()

        #self.dlg.destroy()
        #return response
        pass

    def get_config_widget(self):
        return self.frame

    def hide(self):
        self.cancel_all_threads()

    def on_addfile_clicked(self, *args):
        dialog = gtk.FileChooserDialog( _("Include file..."),
                                        None,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK)
                                        )
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_local_only(False)
        fileFilter = gtk.FileFilter()
        fileFilter.set_name(_("All files"))
        fileFilter.add_pattern("*")
        dialog.add_filter(fileFilter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            fileURI = dialog.get_uri()
            self._add_file(fileURI)
        elif response == gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()

    def on_adddir_clicked(self, *args):
        dialog = gtk.FileChooserDialog( _("Include folder..."),
                                        None,
                                        gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                        (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN,
                                        gtk.RESPONSE_OK)
                                        )
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_local_only(False)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            folderURI = dialog.get_uri()
            self._add_folder(folderURI)
        elif response == gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()
        
    def on_remove_clicked(self, *args):
        (store, rowref) = self.view.get_selection().get_selected()
        if rowref != None:
            path = self.tree_model.get_path(rowref)
            self.db.delete(
                table="config",
                oid=self.tree_model[path][OID_IDX]
                )

    def on_response(self, dialog, response_id):
        """
        Called when the user clicks OK.
        """
        if response_id == gtk.RESPONSE_OK:
            #check the user has specified a named group for all folders
            count, = self.db.select_one("SELECT COUNT(oid) FROM config WHERE TYPE=? and GROUP_NAME=?", (FileDataProvider.TYPE_FOLDER,""))
            if count > 0:
                #stop this dialog from closing, and show a warning to the
                #user indicating that all folders must be named
                warning = gtk.MessageDialog(
                                parent=dialog,
                                flags=gtk.DIALOG_MODAL,
                                type=gtk.MESSAGE_WARNING,
                                buttons=gtk.BUTTONS_OK,
                                message_format=_("Please Name All Folders"))
                warning.format_secondary_text(_("All folders require a descriptive name. To name a folder simply click on it"))
                warning.run()
                warning.destroy()
                dialog.emit_stop_by_name("response")


