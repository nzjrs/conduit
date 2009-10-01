# Banshee-1 support added by Andrew Stormont <andyjstormont@googlemail.com>
# I've tried to keep compatability for Banshee < 1, it should work fine.
# Saved playlists should also be remebered, this all needs testing though.

# FIXME: This doesn't handle folders and never did, should it?

import os
import gobject
import logging
log = logging.getLogger("modules.Banshee")

try:
    #python 2.4
    from pysqlite2 import dbapi2 as sqlite
except ImportError:
    #python 2.5
    from sqlite3 import dbapi2 as sqlite

import conduit
import conduit.utils as Utils
import conduit.Exceptions as Exceptions
import conduit.dataproviders.DataProvider as DataProvider
import conduit.datatypes.Audio as Audio

from gettext import gettext as _

BANSHEE_INSTALLED = False
BANSHEE_VERSION_1 = False
BANSHEE_BASE_LOCATION = ""


if Utils.program_installed("banshee-1"):
    BANSHEE_INSTALLED = True
    BANSHEE_VERSION_1 = True
    import gconf
    BANSHEE_BASE_LOCATION = "file://%s/" % gconf.Client().get_string( "/apps/banshee-1/library/base_location" )
elif Utils.program_installed("banshee"):
    BANSHEE_INSTALLED = True

if BANSHEE_INSTALLED:
    MODULES = {
    	"BansheeSource" : { "type": "dataprovider" }
    }
else:
    MODULES = {}

(ID_IDX, NAME_IDX, CHECKED_IDX, TYPE_IDX) = range( 4 )
(SMART_PLAYLIST, NORMAL_PLAYLIST, VIDEO_PLAYLIST) = range( 1, 4 ) # FIXME should these be hard coded?

class BansheeSource(DataProvider.DataSource):

    _name_ = _("Banshee Playlists")
    _description_ = _("Synchronize your Banshee playlists")
    _category_ = conduit.dataproviders.CATEGORY_MEDIA
    _module_type_ = "source"
    _in_type_ = "file/audio"
    _out_type_ = "file/audio"
    _icon_ = "media-player-banshee"
    _configurable_ = True

    if BANSHEE_VERSION_1:
        MUSIC_DB = os.path.join(os.path.expanduser("~"),".config", "banshee-1", "banshee.db")
    else:
        MUSIC_DB = os.path.join(os.path.expanduser("~"),".config", "banshee", "banshee.db")

    def __init__(self, *args):
        DataProvider.DataSource.__init__(self)
        #Names of the playlists we know
        self.allPlaylists = []
        self.update_configuration(
            #Playlist Ids we wish to sync
            playlists = [],
            smart_playlists = [],
            video_playlists = [],
        )
        self.tracks = []

    def _get_full_uri(self, uri):
        if not uri.startswith("file://"):
            return BANSHEE_BASE_LOCATION + uri

    def _get_all_playlists(self):
        allPlaylists = []
        log.debug("Banshee db %s" % self.MUSIC_DB)
        if os.path.exists(BansheeSource.MUSIC_DB):
            
            #Create a connection to the database
            con = sqlite.connect(BansheeSource.MUSIC_DB)
            cur = con.cursor()
            #Get a list of all playlists for the config dialog
            #If we don't convert all the id's to strings Settings.py will spazz
            if BANSHEE_VERSION_1:
                cur.execute("SELECT PlaylistID, Name FROM CorePlaylists where PrimarySourceID NOT NULL") # NULL = "Play Queue"
                for playlistid, playlistname in cur:
                    allPlaylists.append( {
                        "id"   : str( playlistid ),
                        "name" : playlistname,
                        "type" : NORMAL_PLAYLIST
                    } )
                cur.execute("SELECT SmartPlaylistID, Name FROM CoreSmartPlaylists where PrimarySourceID=%s" % SMART_PLAYLIST)
                for playlistid, playlistname in cur:
                    allPlaylists.append( {
                        "id"   : str( playlistid ),
                        "name" : playlistname,
                        "type" : SMART_PLAYLIST
                    } )
                cur.execute("SELECT SmartPlaylistID, Name FROM CoreSmartPlaylists where PrimarySourceID=%s" % VIDEO_PLAYLIST)
                for playlistid, playlistname in cur:
                    allPlaylists.append( {
                        "id"   : str( playlistid ),
                        "name" : playlistname,
                        "type" : VIDEO_PLAYLIST
                    } )
            else:
                cur.execute("SELECT PlaylistID, Name FROM Playlists")
                for playlistid, playlistname in cur:
                    allPlaylists.append( { 
                        "id"   : str( playlistid ), 
                        "name" : playlistname,
                        "type" : NORMAL_PLAYLIST 
                    } )
            con.close()
        return allPlaylists

    def initialize(self):
        return True

    def is_configured(self, isSource, isTwoWay):
        return len(self.playlists) > 0 or len(self.smart_playlists) > 0 or len(self.video_playlists) > 0
        
    def refresh(self):
        DataProvider.DataSource.refresh(self)
        #only work if Banshee is installed
        if not os.path.exists(BansheeSource.MUSIC_DB):
            raise Exceptions.RefreshError("Banshee is not installed")

        #Stupid pysqlite thread stuff. 
        #Connection must be made in the same thread
        #as any execute statements
        con = sqlite.connect(BansheeSource.MUSIC_DB)
        cur = con.cursor()

        for playlistid in self.playlists:
            if BANSHEE_VERSION_1:
                cur.execute("select Uri from CoreTracks INNER JOIN CorePlaylistEntries ON CorePlaylistEntries.TrackID=CoreTracks.TrackID where PlaylistID=%s" % (playlistid))
            else:
                cur.execute("select Uri from Tracks INNER JOIN PlaylistEntries ON PlaylistEntries.TrackID=Tracks.TrackID where PlaylistID=%s" % (playlistid))
            for Uri in cur:
                self.tracks.append( self._get_full_uri( Uri[0] ) )

        for playlistid in self.smart_playlists + self.video_playlists:
            cur.execute("select Uri from CoreTracks INNER JOIN CoreSmartPlaylistEntries ON CoreSmartPlaylistEntries.TrackID where PlaylistID=%s" % (playlistid))
            for Uri in cur:
                self.tracks.append( self._get_full_uri( Uri[0] ) )
        con.close()

    def get_all(self):
        DataProvider.DataSource.get_all(self)
        return self.tracks

    def get(self, LUID):
        f = Audio.Audio(URI=LUID)
        f.set_UID(LUID)
        f.set_open_URI(LUID)
        return f
    
    def _get_config_playlists(self, config_item):
        playlists = []
        for playlist in self.playlists:
            playlists.append((playlist, NORMAL_PLAYLIST))
        for playlist in self.smart_playlists:
            playlists.append((playlist, SMART_PLAYLIST))
        for playlist in self.video_playlists:
            playlists.append((playlist, VIDEO_PLAYLIST))
        return playlists
        
    def _set_config_playlists(self, config_item, value):
        self.playlists = []
        self.smart_playlists = []
        self.video_playlists = []
        for playlist_id, playlist_type in value:
            {NORMAL_PLAYLIST: self.playlists,
             SMART_PLAYLIST: self.smart_playlists,
             VIDEO_PLAYLIST: self.video_playlists}[playlist_type].append(playlist_id)

    def config_setup(self, config):
        config.add_section(_("Playlists"))        
        self._playlist_config = config.add_item(_("Playlists"), "list",
            initial_value_callback = self._get_config_playlists,
            save_callback = self._set_config_playlists
        )
        
    def config_show(self, config):
        self._all_playlists = self._get_all_playlists()
        playlists = []
        for playlist in self._all_playlists:
            name = playlist['name']
            if playlist['type'] == VIDEO_PLAYLIST:
                name += " (Video)"
            playlists.append(((playlist['id'], playlist['type']), name))
        self._playlist_config.choices = playlists

    def get_UID(self):
        return Utils.get_user_string()


