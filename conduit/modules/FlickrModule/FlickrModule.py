"""
Flickr Uploader.
"""
import logging
log = logging.getLogger("modules.Flickr")

import conduit
import conduit.utils as Utils
import conduit.Web as Web
import conduit.dataproviders.Image as Image
import conduit.Exceptions as Exceptions
import conduit.datatypes.Photo as Photo
from conduit.datatypes import Rid

from gettext import gettext as _

MODULES = {}
try:
    import flickrapi
    if flickrapi.__version__ >= "1.2":
        MODULES = {
        	"FlickrTwoWay" :          { "type": "dataprovider" }        
        }
        log.info("Module Information: %s" % Utils.get_module_information(flickrapi, "__version__"))
        #turn of debugging in the library
        flickrapi.set_log_level(logging.NOTSET)
except ImportError:
    pass

if not MODULES:
    log.info("Flickr support disabled. Please install python-flickrapi > 1.2")
    
class MyFlickrAPI(flickrapi.FlickrAPI):
    """
    Wraps the FlickrAPI in order to override validate_frob to launch the conduit
    web browser.
    """
    #Note that the order, and assignment of values to self.myFrob
    #and self.myToken is important - if done incorrectly then FlickrAPI.__getattr__
    #returns a handler function for them, and not the actual value requested
    def __init__(self, api_key, secret, username):
        flickrapi.FlickrAPI.__init__(self, 
                    api_key=api_key, 
                    secret=secret, 
                    username=username,
                    token=None,
                    format='xmlnode',
                    store_token=True,
                    cache=False
                    )
        self.myFrob = None
        self.myToken = None
                        
    def validate_frob(self, frob, perms):
        self.myFrob = frob
        Web.LoginMagic("Log into Flickr", self.auth_url(perms, frob), login_function=self.try_login)    
            
    def try_login(self):
        try:
            self.myToken = self.get_token(self.myFrob)
            return True
        except flickrapi.FlickrError:
            return False
            
    def login(self):
        token, frob = self.get_token_part_one(perms='delete')
        if token:
            log.debug("Got token from cache")
            return token
        else:
            log.debug("Got token from web")
            return self.myToken

class FlickrTwoWay(Image.ImageTwoWay):

    _name_ = _("Flickr")
    _description_ = _("Synchronize your Flickr.com photos")
    _module_type_ = "twoway"
    _icon_ = "flickr"
    _configurable_ = True

    API_KEY="65552e8722b21d299388120c9fa33580"
    SHARED_SECRET="03182987bf7fc4d1"

    def __init__(self, *args):
        Image.ImageTwoWay.__init__(self)
        self.fapi = None
        self.token = None
        self.logged_in = False
        self.photoSetId = None
        self.update_configuration(
            imageSize = "None",
            username = ("", self._set_username),
            photoSetName = "",
            showPublic = True
        )

    # Helper methods
    def _get_user_quota(self):
        """
        Returs used,total or -1,-1 on error
        """
        try:
            ret = self.fapi.people_getUploadStatus()
            totalkb =   int(ret.user[0].bandwidth[0]["maxkb"])
            usedkb =    int(ret.user[0].bandwidth[0]["usedkb"])
            p = (float(usedkb)/totalkb)*100.0
            return usedkb,totalkb,p
        except flickrapi.FlickrError, e:
            log.debug("Error getting quota: %s" % e)
            return -1,-1,100

    def _get_photo_info(self, photoID):
        try:
            return self.fapi.photos_getInfo(photo_id=photoID)
        except flickrapi.FlickrError, e:
            log.debug("Error getting photo info: %s" % e)
            return None

    def _get_raw_photo_url(self, photoInfo):
        photo = photoInfo.photo[0]
        #photo is a dict so we can use pythons string formatting natively with the correct keys
        url = "http://farm%(farm)s.static.flickr.com/%(server)s/%(id)s_%(secret)s.jpg" % photo
        return url

    def _upload_photo (self, uploadInfo):
        try:
            ret = self.fapi.upload( 
                                filename=uploadInfo.url,
                                title=uploadInfo.name,
                                description=uploadInfo.caption,
                                is_public="%i" % self.showPublic,
                                tags=' '.join(tag.replace(' ', '_') for tag in uploadInfo.tags))
        except flickrapi.FlickrError, e:
            raise Exceptions.SyncronizeError("Flickr Upload Error: %s" % e)

        # get the id
        photoId = ret.photoid[0].text

        # check if phtotoset exists, if not create it
        firstPhoto = False
        if not self.photoSetId:
            self.photoSetId = self._create_photoset(photoId)
            # first photo shouldn't be added to photoset as Flickrs does it for us
            firstPhoto = True

        # add the photo to the photoset
        if self.photoSetId and not firstPhoto:
            try:
                ret = self.fapi.photosets_addPhoto(
                                    photoset_id = self.photoSetId,
                                    photo_id = photoId)
            except flickrapi.FlickrError, e:
                log.warn("Flickr failed to add %s to set: %s" % (photoId,e))

        #return the photoID
        return Rid(uid=photoId)

    def _get_photo_size (self):
        return self.imageSize

    def _set_username(self, username):
        if self.username != username:
            self.username = username
            self.logged_in = False        

    def _login(self):
        #only log in if we need to
        if not self.logged_in:
            self.fapi = MyFlickrAPI(FlickrTwoWay.API_KEY, FlickrTwoWay.SHARED_SECRET, self.username)
            self.token = self.fapi.login()
            self.logged_in = True
            
    def _create_photoset(self, primaryPhotoId):
        #create one with created photoID if not
        try:
            ret = self.fapi.photosets_create(
                                    title=self.photoSetName,
                                    primary_photo_id=primaryPhotoId)
            return ret.photoset[0]['id']
        except flickrapi.FlickrError, e:
            log.warn("Flickr failed to create photoset %s: %s" % (self.photoSetName,e))
            return None
                
    def _get_photoset(self):
        for name, photoSetId in self._get_photosets():
            if name == self.photoSetName:
                log.debug("Found album %s" % self.photoSetName)
                self.photoSetId = photoSetId
                
    def _get_photosets(self):
        photosets = []
        try:
            ret = self.fapi.photosets_getList()  
            if hasattr(ret.photosets[0], 'photoset'):
                for pset in ret.photosets[0].photoset:
                    photosets.append(
                                (pset.title[0].text,        #photoset name
                                pset['id']))                #photoset id
        except flickrapi.FlickrError, e:
            log.debug("Failed to get photosets: %s" % e)

        return photosets        
        
    def _get_photos(self):
        if not self.photoSetId:
            return []

        photoList = []
        try:
            ret = self.fapi.photosets_getPhotos(photoset_id=self.photoSetId)
            for photo in ret.photoset[0].photo:
                photoList.append(photo['id'])
        except flickrapi.FlickrError, e:
            log.warn("Flickr failed to get photos: %s" % e)

        return photoList
        
    # DataProvider methods
    def refresh(self):
        Image.ImageTwoWay.refresh(self)
        self._login()
        self._get_photoset()
        used,tot,percent = self._get_user_quota()
        log.debug("Used %2.1f%% of monthly badwidth quota (%skb/%skb)" % (percent,used,tot))

    def get_all(self):
        return self._get_photos()

    def get (self, LUID):
        # get photo info
        photoInfo = self._get_photo_info(LUID)
        # get url
        url = self._get_raw_photo_url (photoInfo)
        # get the title
        title = str(photoInfo.photo[0].title[0].text)
        # get tags
        tagsNode = photoInfo.photo[0].tags[0]
        # get caption
        caption = photoInfo.photo[0].description[0].text
        
        if hasattr(tagsNode, 'tag'):
            tags = tuple(tag.text for tag in tagsNode.tag)
        else:
            tags = ()

        # create the file
        f = Photo.Photo (URI=url)
        f.set_open_URI(url)
        f.set_caption(caption)

        # try to rename if a title is available
        # FIXME: this is far from optimal, also there should be 
        # a way to get out the originals
        if title:
            if not title.endswith('jpg'):
                title = title + '.jpg'
            f.force_new_filename(title)

        f.set_UID(LUID)

        # set the tags
        f.set_tags (tags)

        return f

    def delete(self, LUID):
        if self._get_photo_info(LUID) != None:
            try:
                ret = self.fapi.photos_delete(photo_id=LUID)
                log.debug("Successfully deleted photo: %s" % LUID)
            except flickrapi.FlickrError, e:
                log.warn("Error deleting %s: %s" % (LUID,e))
        else:
            log.warn("Error deleting %s: doesnt exist" % LUID)

    def config_setup(self, config):
              
        def _login_finished(*args):
            try:
                if self.logged_in:
                    config['status'].value = _('Loading album list...')
                    try:
                        #FIXME: Blocks and brings the whole UI with it.
                        photosets = self._get_photosets()
                    except:
                        config['status'].value = _('Failed to connect.')
                    else:
                        config['photoSetName'].choices = [name for name, photoSetId in photosets]
                        config['status'].value = _('Album names loaded.')
                else:
                    config['status'].value = _('Failed to login.')
            finally:
                config['photoSetName'].enabled = True
                account_section.enabled = True
                config.set_busy(False)
                
        def _load_photosets(button):
            config.set_busy(True)
            config['photoSetName'].enabled = False
            account_section.enabled = False
            username_config.apply()
            config['status'].value = _('Logging in, please wait...')
            conduit.GLOBALS.syncManager.run_blocking_dataprovider_function_calls(
                self, _login_finished, self._login)

        account_section = config.add_section(_('Account details'))
        username_config = config.add_item(_('Username'), 'text',
            config_name = 'username',
        )
        username_config.connect('value-changed',
            lambda item, initial, value: load_photosets_config.set_enabled(bool(value)))
        status_label = config.add_item(None, 'label',
            name = 'status',
            initial_value = self.status,
            use_markup = True,
            xalignment = 0.5,
        )
        load_photosets_config = config.add_item(_("Authenticate"), "button",
            initial_value = _load_photosets,
            image = "dialog-password"
        )
        config.add_section(_('Saved photo settings'))
        photoset_config = config.add_item('Photoset name', 'combotext',
            config_name = 'photoSetName',
            choices = [],
        )
        config.add_item(_("Resize photos"), "combo",
            choices = [("None", _("Do not resize")), _("640x480"), _("800x600"), _("1024x768")],
            config_name = "imageSize"
        )
        config.add_item(_('Photos are public'), 'check',
            config_name = 'showPublic'
        )
       
    def is_configured (self, isSource, isTwoWay):
        return len(self.username) > 0 and len(self.photoSetName) > 0
        
    def get_UID(self):
        return self.token
            
