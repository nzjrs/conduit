import gobject
import urllib
import os.path
import time

import logging
log = logging.getLogger("Vfs")

import conduit
import conduit.utils.Singleton as Singleton

import File as File

def backend_supports_remote_uri_schemes():
    """
    @returns: True if the file implementation supports non-local (file://)
    uri schemes
    """
    return True

def backend_name():
    """
    @returns: The name of the selected file impl backend
    """
    return "GIO"

#FIXME: g_vfs_get_supported_uri_schemes needs to be wrapped
def uri_is_valid(uri):
    """
    Checks if the uri is valid (i.e. not a local path), and its type
    is supported by the underlying file implementation
    """
    SCHEMES = ("file://","http://","ftp://","smb://")

    return uri[0] != "/" and uri.split("://")[0]+"://" in SCHEMES

def uri_join(first, *rest):
    """
    Joins multiple uri components. Performs safely if the first
    argument contains a uri scheme
    """
    return File.File.uri_join(first,*rest)

def uri_get_scheme(uri):
    """
    @returns: The scheme (file,smb,ftp) for the uri, or None on error
    """
    return File.File.uri_get_scheme(uri)
    
def uri_get_relative(fromURI, toURI):
    """
    Returns the relative path fromURI --> toURI
    """
    return File.File.uri_get_relative(fromURI, toURI)
    
def uri_open(uri):
    """
    Opens a xdg compatible uri.
    """
    uri = conduit.utils.ensure_string(uri)
    APP = "xdg-open"
    os.spawnlp(os.P_NOWAIT, APP, APP, uri)
    
def uri_to_local_path(uri):
    """
    @returns: The local path (/foo/bar) for the given URI
    """
    uri = conduit.utils.ensure_string(uri)
    scheme = uri_get_scheme(uri)
    if scheme == "file":
        #len("file://") = 7
        return uri[7:]
    else:
        return None
    
def uri_get_volume_root_uri(uri):
    """
    @returns: The root path of the volume at the given uri, or None
    """
    f = File.File(uri)
    return f.get_removable_volume_root_uri()
    
def uri_is_on_removable_volume(uri):
    """
    @returns: True if the specified uri is on a removable volume, like a USB key
    or removable/mountable disk.
    """
    f = File.File(uri)
    return f.is_on_removale_volume()

def uri_get_filesystem_type(uri):
    """
    @returns: The filesystem that uri is stored on or None if it cannot
    be determined
    """
    f = File.File(uri)
    return f.get_filesystem_type()

def uri_escape(uri):
    """
    Escapes a uri, replacing only special characters that would not be found in 
    paths or host names.
    (so '/', '&', '=', ':' and '@' will not be escaped by this function)
    """
    import urllib
    uri = conduit.utils.ensure_string(uri)
    return urllib.quote(uri,safe='/&=:@')
    
def uri_unescape(uri):
    """
    Replace "%xx" escapes by their single-character equivalent.
    """
    import urllib
    uri = conduit.utils.ensure_string(uri)
    return urllib.unquote(uri)
    
def uri_get_protocol(uri):
    """
    Returns the protocol (file, smb, etc) for a URI
    """
    uri = conduit.utils.ensure_string(uri)
    if uri.rfind("://")==-1:
        return ""
    protocol = uri[:uri.index("://")+3]
    return protocol.lower()

def uri_get_filename(uri):
    """
    Method to return the filename of a file.
    """
    uri = conduit.utils.ensure_string(uri)
    return uri.split(os.sep)[-1]

def uri_get_filename_and_extension(uri):
    """
    Returns filename,file_extension
    """
    uri = conduit.utils.ensure_string(uri)
    return os.path.splitext(uri_get_filename(uri))
    
def uri_sanitize_for_filesystem(uri, filesystem=None):
    """
    Removes illegal characters in uri that cannot be stored on the 
    given filesystem - particuarly fat and ntfs types
    
    Also see:    
    http://bugzilla.gnome.org/show_bug.cgi?id=309584#c20
    """
    
    uri = conduit.utils.ensure_string(uri)
    import string

    ILLEGAL_CHARS = {
        "fat"       :   "\\:*?\"<>|",
        "vfat"      :   "\\:*?\"<>|",
        "msdos"     :   "\\:*?\"<>|",
        "msdosfs"   :   "\\:*?\"<>|",
        "ntfs"      :   "\\:*?\"<>|"
    }

    illegal = ILLEGAL_CHARS.get(filesystem,None)
    if illegal:
        
        #call urllib.unescape otherwise for example ? is rapresented as %3F
        uri = urllib.unquote(uri)

        #dont escape the scheme part
        idx = uri.rfind("://")
        if idx == -1:
            start = 0
        else:
            start = idx + 3        

        #replace illegal chars with a -, ignoring the scheme (don't use a space because you can't create a directory with just a space)
        ret = uri[0:start]+uri[start:].translate(string.maketrans(
                illegal,
                "_"*len(illegal)
                )
                                                 )
        ret = uri[0:start]+urllib.quote (ret[start:])
        return ret
    return uri
    
def uri_is_folder(uri):
    """
    @returns: True if the uri is a folder and not a file
    """
    f = File.File(uri)
    return f.is_directory()
    
def uri_format_for_display(uri):
    """
    Formats the uri so it can be displayed to the user (strips passwords, etc)
    """
    f = File.File(uri)
    return f.get_uri_for_display()
    
def uri_exists(uri):
    """
    @returns: True if the uri exists
    """
    f = File.File(uri)
    return f.exists()

