import gio
import gobject
import time
import threading
import os.path
import logging
log = logging.getLogger("vfs.File")

class File:
    NAME = "GIO"
    def __init__(self, URI, impl=None):
        if impl:
            self._file = impl
        else:
            self._file = gio.File(URI)
        self.close()

    def _get_file_info(self):
        if not self.triedOpen:
            try:
                #FIXME: Only get attributes we actually care about
                self.fileInfo = self._file.query_info("standard::*,time::*")
                #for ns in ("standard","time"):
                #    log.info("%s Attributes: %s" % (
                #            ns.title(),
                #            ','.join(self.fileInfo.list_attributes(ns)))
                #            )
                self.fileExists = True
            except gio.Error:
                self.fileExists = False
            self.triedOpen = True

    def get_text_uri(self):
        return self._file.get_uri()
        
    def get_local_path(self):
        return self._file.get_path()
        
    def is_local(self):
        return self._file.is_native()
        
    def is_directory(self):
        self._get_file_info()
        return self.fileInfo.get_file_type() == gio.FILE_TYPE_DIRECTORY
        
    def delete(self):
        try:
            #FIXME: Trash first?
            self._file.delete()
            self.close()
        except gio.Error, e:
            log.warn("File delete error: %s" % e)
        
    def exists(self):
        self._get_file_info()
        return self.fileExists
        
    def set_mtime(self, timestamp=None, datetime=None):
        try:
            if self._file.set_attribute_uint64("time::modified", long(timestamp)):
                self.close()
                return timestamp
            else:
                return None
        except gio.Error, e:
            return None
        
    def set_filename(self, filename):
        try:
            self._file = self._file.set_display_name(filename)
            self.close()
            return filename
        except gio.Error, e:
            return None
        
    def get_mtime(self):
        self._get_file_info()
        mtime = self.fileInfo.get_attribute_uint64('time::modified')
        if mtime:
            return mtime
        else:
            #convert 0L -> None
            return None

    def get_filename(self):
        self._get_file_info()
        return self.fileInfo.get_display_name()

    def get_uri_for_display(self):
        return self._file.get_parse_name()
        
    def get_contents(self):
        contents,length,etag = self._file.load_contents()
        return contents

    def set_contents(self, contents):
        self._file.replace_contents(contents)
        self.close()
        
    def get_mimetype(self):
        self._get_file_info()
        return self.fileInfo.get_attribute_string('standard::content-type')

    def get_size(self):
        self._get_file_info()
        return self.fileInfo.get_size()

    def close(self):
        self.fileInfo = None
        self.fileExists = False
        self.triedOpen = False

    def make_directory(self):
        try:
            result = self._file.make_directory()
            self.close()
            return result
        except gio.Error, e:
            return False

    def make_directory_and_parents(self):
        #recursively create all parent dirs if needed
        #port the code from gio into python until the following is fixed
        #http://bugzilla.gnome.org/show_bug.cgi?id=546575
        dirs = []

        try:
            result = self._file.make_directory()
            code = 0;
        except gio.Error, e:
            result = False
            code = e.code

        work_file = self._file
        while code == gio.ERROR_NOT_FOUND and not result:
            parent_file = work_file.get_parent()
            if not parent_file:
                break

            try:
                result = parent_file.make_directory()
                code = 0;
            except gio.Error, e:
                result = False
                code = e.code

            if code == gio.ERROR_NOT_FOUND and not result:
                dirs.append(parent_file)

            work_file = parent_file;

        #make all dirs in reverse order
        dirs.reverse()
        for d in dirs:
            try:
                result = d.make_directory()
            except gio.Error:
                result = False
                break

        #make the final dir
        if result:
            try:
                result = self._file.make_directory()
            except gio.Error:
                result = False

        self.close()
        return result

    def is_on_removale_volume(self):
        try:
            return self._file.find_enclosing_mount().can_unmount()
        except gio.Error:
            return False

    def get_removable_volume_root_uri(self):
        try:
            return self._file.find_enclosing_mount().get_root().get_uri()
        except gio.Error:
            return None

    def get_filesystem_type(self):
        try:
            info = self._file.query_filesystem_info("filesystem::type")
            return info.get_attribute_string("filesystem::type")
        except gio.Error, e:
            return None

    @staticmethod
    def uri_join(first, *rest):
        return os.path.join(first, *rest)

    @staticmethod
    def uri_get_relative(fromURI, toURI):
        f = gio.File(fromURI)
        t = gio.File(toURI)
        res = f.get_relative_path(t)
        #if not relative, return abs path
        if not res:
            res = toURI
        return res

    @staticmethod
    def uri_get_scheme(URI):
        f = gio.File(URI)
        return f.get_uri_scheme()

class FileTransfer:
    def __init__(self, source, dest):
        self._source = source._file
        self._dest = gio.File(dest)
        self._cancel_func = lambda : False
        self._cancellable = gio.Cancellable()
        
    def _xfer_progress_callback(self, current, total):
        #check if cancelled
        try:
            if self._cancel_func():
                log.info("Transfer of %s -> %s cancelled" % (self._source.get_uri(), self._dest.get_uri()))
                self._cancellable.cancel()
        except Exception:
            log.warn("Could not call transfer cancel function", exc_info=True)
        return True
        
    def set_destination_filename(self, name):
        #if it exists and its a directory then transfer into that dir
        #with the new filename
        try:
            info = self._dest.query_info("standard::name,standard::type")
            if info.get_file_type() == gio.FILE_TYPE_DIRECTORY:
                self._dest = self._dest.get_child(name)
        except gio.Error:
            #file does not exist
            pass

    def transfer(self, overwrite, cancel_func):
        if cancel_func:
            self._cancel_func = cancel_func
    
        if overwrite:
            mode = gio.FILE_COPY_OVERWRITE
        else:
            mode = gio.FILE_COPY_NONE

        log.debug("Transfering File %s -> %s (overwrite: %s)" % (self._source.get_uri(), self._dest.get_uri(), overwrite))

        #recursively create all parent dirs if needed
        parent = self._dest.get_parent()
        try:
            parent.query_info("standard::name")
        except gio.Error, e:
            #does not exists
            d = File(None, impl=parent)
            d.make_directory_and_parents()

        #Copy the file
        try:      
            ok = self._source.copy(
                        destination=self._dest,
                        flags=mode|gio.FILE_COPY_ALL_METADATA,
                        cancellable=self._cancellable,
                        progress_callback=self._xfer_progress_callback
                        )
            return ok, File(None, impl=self._dest)
        except gio.Error, e:
            log.warn("File transfer error: %s" % e)
            return False, None

class FolderScanner(threading.Thread, gobject.GObject):
    """
    Recursively scans a given folder URI, returning the number of
    contained files.
    """

    __gsignals__ =  { 
                    "scan-progress": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [
                        gobject.TYPE_INT]),
                    "scan-completed": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
                    }
    CONFIG_FILE_NAME = ".conduit.conf"

    def __init__(self, baseURI, includeHidden, followSymlinks):
        threading.Thread.__init__(self)
        gobject.GObject.__init__(self)
        self.baseURI = str(baseURI)
        self.includeHidden = includeHidden
        self.followSymlinks = followSymlinks
        self.dirs = [self.baseURI]
        self.cancelled = False
        self.URIs = []
        self.setName("FolderScanner Thread: %s" % self.baseURI)

    def run(self):
        """
        Recursively adds all files in dirs within the given list.
        
        Code adapted from Listen (c) 2006 Mehdi Abaakouk
        (http://listengnome.free.fr/)
        """
        delta = 0
        t = 1
        last_estimated = estimated = 0 
        while len(self.dirs)>0:
            if self.cancelled:
                return

            dir = self.dirs.pop(0)
            try: 
                f = gio.File(dir)
                enumerator = f.enumerate_children('standard::type,standard::name,standard::is-hidden,standard::is-symlink')
            except gio.Error:
                log.warn("Folder %s Not found" % dir, exc_info=True)
                continue

            try: 
                fileinfo = enumerator.next()
            except StopIteration:
                enumerator.close()
                continue
            while fileinfo:
                filename = fileinfo.get_name()
                filetype = fileinfo.get_file_type()
                hidden = fileinfo.get_is_hidden()
                if filename != self.CONFIG_FILE_NAME:
                    if filetype == gio.FILE_TYPE_DIRECTORY:
                        #Include hidden directories
                        if not hidden or self.includeHidden:
                            self.dirs.append(dir+"/"+filename)
                            t += 1
                    elif filetype == gio.FILE_TYPE_REGULAR or (filetype == gio.FILE_TYPE_SYMBOLIC_LINK and self.followSymlinks):
                            uri = dir+"/"+filename
                            #Include hidden files
                            if not hidden or self.includeHidden:
                                self.URIs.append(uri)
                    else:
                        log.debug("Unsupported file type: %s (%s)" % (filename, filetype))
                try: 
                    fileinfo = enumerator.next()
                except StopIteration:
                    enumerator.close()
                    break

            #Calculate the estimated complete percentags
            estimated = 1.0-float(len(self.dirs))/float(t)
            estimated *= 100
            #Enly emit progress signals every 10% (+/- 1%) change to save CPU
            if delta+10 - estimated <= 1:
                log.debug("Folder scan %s%% complete" % estimated)
                self.emit("scan-progress", len(self.URIs))
                delta += 10
            last_estimated = estimated

        i = 0
        total = len(self.URIs)
        log.debug("%s files loaded" % total)
        self.emit("scan-completed")

    def cancel(self):
        """
        Cancels the thread as soon as possible.
        """
        self.cancelled = True

    def get_uris(self):
        return self.URIs

class FolderScannerThreadManager:
    """
    Manages many FolderScanner threads. This involves joining and cancelling
    said threads, and respecting a maximum num of concurrent threads limit
    """
    def __init__(self, maxConcurrentThreads=2):
        self.maxConcurrentThreads = maxConcurrentThreads
        self.scanThreads = {}
        self.pendingScanThreadsURIs = []

    def make_thread(self, folderURI, includeHidden, followSymlinks, progressCb, completedCb, *args):
        """
        Makes a thread for scanning folderURI. The thread callsback the model
        at regular intervals with the supplied args
        """
        running = len(self.scanThreads) - len(self.pendingScanThreadsURIs)

        if folderURI not in self.scanThreads:
            thread = FolderScanner(folderURI, includeHidden, followSymlinks)
            thread.connect("scan-progress", progressCb, *args)
            thread.connect("scan-completed", completedCb, *args)
            thread.connect("scan-completed", self._register_thread_completed, folderURI)
            self.scanThreads[folderURI] = thread
            if running < self.maxConcurrentThreads:
                log.debug("Starting thread %s" % folderURI)
                self.scanThreads[folderURI].start()
            else:
                self.pendingScanThreadsURIs.append(folderURI)
            return thread
        else:
            return self.scanThreads[folderURI]

    def _register_thread_completed(self, sender, folderURI):
        """
        Decrements the count of concurrent threads and starts any 
        pending threads if there is space
        """
        #delete the old thread
        del(self.scanThreads[folderURI])
        running = len(self.scanThreads) - len(self.pendingScanThreadsURIs)

        log.debug("Thread %s completed. %s running, %s pending" % (folderURI, running, len(self.pendingScanThreadsURIs)))

        if running < self.maxConcurrentThreads:
            try:
                uri = self.pendingScanThreadsURIs.pop()
                log.debug("Starting pending thread %s" % uri)
                self.scanThreads[uri].start()
            except IndexError: pass

    def join_all_threads(self):
        """
        Joins all threads (blocks)

        Unfortunately we join all the threads do it in a loop to account
        for join() a non started thread failing. To compensate I time.sleep()
        to not smoke CPU
        """
        joinedThreads = 0
        while(joinedThreads < len(self.scanThreads)):
            for thread in self.scanThreads.values():
                try:
                    thread.join()
                    joinedThreads += 1
                except (RuntimeError, AssertionError):
                    #deal with not started threads
                    time.sleep(0.1)

    def cancel_all_threads(self):
        """
        Cancels all threads ASAP. My block for a small period of time
        because we use our own cancel method
        """
        for thread in self.scanThreads.values():
            if thread.isAlive():
                log.debug("Cancelling thread %s" % thread)
                thread.cancel()
            thread.join() #May block

class MultipleFileMonitor(gobject.GObject):
    """
    Abstraction which makes it easy to monitor multiple files
    for changes
    """

    __gsignals__ = {
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [
            gobject.TYPE_PYOBJECT,      #uri that changed
            gobject.TYPE_PYOBJECT])     #event type
        }

    MONITOR_EVENT_CREATED =             gio.FILE_MONITOR_EVENT_CREATED
    MONITOR_EVENT_CHANGED =             gio.FILE_MONITOR_EVENT_CHANGED
    MONITOR_EVENT_DELETED =             gio.FILE_MONITOR_EVENT_DELETED
    MONITOR_DIRECTORY =                 255

    def __init__(self):
        gobject.GObject.__init__(self)
        self._fm = None

    def _on_change(self, monitor, f1, f2, event):
        self.emit("changed", f1.get_uri(), event)

    def add(self, URI, monitorType):
        try:
            if monitorType == self.MONITOR_DIRECTORY:
                self._fm = gio.File(URI).monitor_directory()
            else:
                self._fm = gio.File(URI).monitor_file()

            self._fm.connect("changed", self._on_change)
        except gio.Error:
            log.warn("Could not add monitor", exc_info=True)

    def cancel(self):
        if self._fm:
            try:
                self._fm.disconnect_by_func(self._on_change)
            except TypeError:
                pass


