"""
Facebook Photo Uploader.
"""
import os, sys
import traceback
import md5
import logging
log = logging.getLogger("modules.Facebook")

import conduit
import conduit.utils as Utils
import conduit.Web as Web
import conduit.dataproviders.Image as Image
import conduit.Exceptions as Exceptions
from conduit.datatypes import Rid
import conduit.datatypes.File as File

from gettext import gettext as _

try:
    import pyfacebook
except ImportError:
    Utils.dataprovider_add_dir_to_path(__file__)
    import pyfacebook
    
if pyfacebook.VERSION < '0.1':
    log.info("Facebook support disabled")
    MODULES = {}
else:
    log.info("Module Information: %s" % Utils.get_module_information(pyfacebook, 'VERSION'))
    log.info("Facebook parsing using: %s (%s)" % (pyfacebook.RESPONSE_FORMAT, getattr(pyfacebook, "JSON_MODULE", "N/A")))
    MODULES = {
        "FacebookSink" :          { "type": "dataprovider" }        
    }

class FacebookSink(Image.ImageSink):

    _name_ = _("Facebook")
    _description_ = _("Synchronize your Facebook photos")
    _module_type_ = "sink"
    _icon_ = "facebook"
    _configurable_ = True

    API_KEY="6ce1868c3292471c022c771c0d4d51ed"
    SECRET="20e2c82829f1884e40efc616a44e5d1f"

    def __init__(self, *args):
        Image.ImageSink.__init__(self)
        self.fapi = pyfacebook.Facebook(FacebookSink.API_KEY, FacebookSink.SECRET)
        self.browser = conduit.BROWSER_IMPL
        self.update_configuration(
            albumname = ""
        )
        self.albums = {}

    def _upload_photo (self, uploadInfo):
        """
        Upload to album; and return image id here
        """
        try:
            rsp = self.fapi.photos.upload(
                                        uploadInfo.url,
                                        aid=self.albums.get(self.albumname, None))
            pid = str(rsp["pid"])
            return Rid(uid=pid)
        except pyfacebook.FacebookError, f:
            raise Exceptions.SyncronizeError("Facebook Upload Error %s" % f)
            
    def _get_albums(self):
        albums = {}
        try:
            for a in self.fapi.photos.getAlbums(self.fapi.uid):
                albums[a['name']] = a['aid']
        except pyfacebook.FacebookError, f:
            log.warn("Error getting album list: %s" % f)
        return albums
        
    def _get_photos(self, albumID):
        photos = {}
        try:
            for p in self.fapi.photos.get(aid=albumID):
                #only return big photos
                if p.get("src_big", ""):
                    pid = str(p["pid"])
                    photos[pid] = p
        except pyfacebook.FacebookError, f:
            log.warn("Error getting photos from album %s list: %s" % (albumID,f))
        return photos
        
    def _get_photo_size (self):
        """
        Respect Facebooks largest image dimension of 604px
        http://wiki.developers.facebook.com/index.php/Photos.upload
        """
        return "604x604"        

    def _login(self):
        """
        Get ourselves a token we can use to perform all calls
        """
        self.fapi.auth.createToken()
        url = self.fapi.get_login_url()

        #wait for log in
        Web.LoginMagic("Log into Facebook", url, login_function=self._try_login, 
                browser=self.browser,       #instance var so tests can set it to system
                sleep_time=45,              #long sleep time to give time to login if using system browser
                )

    def _try_login(self):
        """
        This function is used by the login tester, we try to get a token,
        but return None if it does not succeed so the login tester can keep trying
        """
        log.info("Trying Login")
        rsp = self.fapi.auth.getSession()
        return rsp.has_key("secret") and rsp.has_key("session_key")
        
    def config_setup(self, config):

        def _login_finished(*args):
            try:
                if self.fapi.uid:
                    status_label.value = _('Loading album list...')
                    try:
                        albums = self._get_albums().keys()
                    except:
                        status_label.value = _('Failed to connect')
                    else:
                        albums_config.choices = albums
                        status_label.value = _('Logged in')
                else:
                    status_label.value = _('Failed to login')
            finally:
                album_section.enabled = True
                config.set_busy(False)

        def _load_albums(button):
            config.set_busy(True)
            album_section.enabled = False
            status_label.value = 'Logging in, please wait...'
            conduit.GLOBALS.syncManager.run_blocking_dataprovider_function_calls(
                self, _login_finished, self._login)

        status_label = config.add_item(_('Status'), 'label',
            initial_value = "Logged in" if self.fapi.uid else "Not logged in",
            use_markup = True,
        )

        album_section = config.add_section(_("Album"))
        albums_config = config.add_item(_("Album name"), "combotext",
            config_name = "albumname",
            choices = [],
        )
        
        load_albums_config = config.add_item(_("Load albums"), "button",
            initial_value = _load_albums
        )                    
        
    def refresh(self):
        Image.ImageSink.refresh(self)
        if self.fapi.uid == None:
            self._login()

        #get the list of albums
        if self.fapi.uid:
            self.albums = self._get_albums()
            if self.albumname and self.albumname not in self.albums:
                log.info("Creating album: %s" % self.albumname)
                try:
                    rsp = self.fapi.photos.createAlbum(
                                              #session_key=self.fapi.session_key,
                                              name=self.albumname)
                    self.albums[self.albumname] = rsp["aid"]
                except pyfacebook.FacebookError, f:
                    self.albumname = ""
                    log.warn("Error creating album: %s" % self.albumname)

    def get_UID(self):
        if self.fapi.uid == None:
            return ""
        return self.fapi.uid
        
    def is_configured (self, isSource, isTwoWay):
        #Specifing an album is optional
        return True
