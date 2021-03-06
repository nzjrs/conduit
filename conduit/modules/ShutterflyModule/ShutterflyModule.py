"""
Shutterfly Data Sink
"""
import logging
log = logging.getLogger("modules.Shutterfly")

import conduit
import conduit.utils as Utils
from conduit.datatypes import Rid
import conduit.dataproviders.Image as Image
import conduit.Exceptions as Exceptions
import conduit.datatypes.Photo as Photo

Utils.dataprovider_add_dir_to_path(__file__, "shutterfly")
from shutterfly import Shutterfly

from gettext import gettext as _

MODULES = {
	"ShutterflySink" : {"type" : "dataprovider"},
}


class ShutterflySink(Image.ImageSink):
	
	_name_ = _("Shutterfly")
	_description_ = _("Synchronize your Shutterfly photos")
	_module_type_ = "sink"
	_icon_ = "shutterfly"
	_configurable_ = True
	
	def __init__(self, *args):
		Image.ImageSink.__init__(self)
		self.update_configuration(
			username = "",
			password = "",
			album = ""
		)
		self.sapi = None
		self.salbum = None
		self.sphotos = None

	def _get_raw_photo_url(self, photoInfo):
		return photoInfo.url

	def _get_photo_info(self, id):
		if self.sphotos.has_key(id):
			return self.sphotos[id]
		else:
			return None
	
	def _get_photo_formats(self):
		return ("image/jpeg", )
	
	def refresh(self):
		Image.ImageSink.refresh(self)
		self.sapi = Shutterfly(self.username, self.password)
		
		albums = self.sapi.getAlbums()
		if not albums.has_key(self.album):
			self.salbum = self.sapi.createAlbum(self.album)
		else:
			self.salbum = albums[self.album]
		
		self.sphotos = self.salbum.getPhotos()
	
	def get_all(self):
		return self.sphotos.keys()
	
	def get(self, LUID):
		#Image.ImageSink.get(self, LUID)
		sphoto = self.sphotos[LUID]

		f = Photo.Photo(URI=sphoto.url)
		f.set_open_URI(sphoto.url)
		f.set_UID(LUID)

		return f

	def delete(self, LUID):
		"""
		Delete a photo by ID
		Deleting a photo invalidates album length and photo index values.
		We must reload the photos (or do something else...)
		"""
		if not self.sphotos.has_key(LUID):
			log.warn("Photo does not exist")
			return

		try:
			self.salbum.deletePhoto(self.sphotos[LUID])
		except Exception, e:
			raise Exceptions.SyncronizeError("Shutterfly Delete Error - Try Again.")

		self.sphotos = self.salbum.getPhotos()
		
	def _upload_photo(self, uploadInfo):
		"""
		Upload to album
		"""
		try:
			ret = self.salbum.uploadPhoto(uploadInfo.url, uploadInfo.mimeType, uploadInfo.name)
			return Rid(ret.id)
		except Exception, e:
			raise Exceptions.SyncronizeError("Shutterfly Upload Error.")
	
	def config_setup(self, config):
		config.add_section('Account details')
		config.add_item('Username', 'text',
			config_name = 'username',
		)
		config.add_item('Password', 'text',
			config_name = 'password',
			password = True
		)
		config.add_section('Saved photo settings')
		config.add_item('Album', 'text',
			config_name = 'album',
		)
	
	def is_configured(self, isSource, isTwoWay):
		if len(self.username) < 1:
			return False
		if len(self.password) < 1:
			return False
		if len(self.album) < 1:
			return False
		return True
	
	def get_UID(self):
		return self.username+":"+self.album

