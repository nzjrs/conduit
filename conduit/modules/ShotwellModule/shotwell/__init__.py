import os.path
import sqlite3
import string
import sys

class Version(object):


    def __init__(self, schemaVersion, appVersion, userData=None):
        self._schemaVersion = schemaVersion
        self._appVersion = appVersion
        self._userData = userData

    def __str__(self):
        return 'Version(' + str(map(lambda key: str(key) + '=' +
               str(self.__dict__[key]), self.__dict__.keys())) + ')'

    @property
    def schemaVersion(self):
        return self._schemaVersion

    @property
    def appVersion(self):
        return self._appVersion

    @property
    def userData(self):
        return self._userData


class Event(object):


    def __init__(self, id, name):
        self._id = id
        self._name = name

    def __str__(self):
        return 'Event(' + str(map(lambda key: str(key) + '=' +
               str(self.__dict__[key]), self.__dict__.keys())) + ')'

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name


class Tag(object):


    def __init__(self, id, name, photo_id_list_csv):
        self._id = id
        self._name = name
        self._photoIDs = filter(lambda x: x != None and len(x) > 0,
                                string.split(photo_id_list_csv, ','))

    def __str__(self):
        return 'Tag(id=' + str(self.id) + ';name=' + str(self.name) + \
               ';num photos=' + str(len(self.photoIDs)) + ')'

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def photoIDs(self):
        return self._photoIDs


class Photo(object):


    def __init__(self, id, filename, width=None, height=None, filesize=None,
                 timestamp=None, eventID=None, title=''):
        self._id = id
        self._filename = filename
        self._width = width
        self._height = height
        self._filesize = filesize
        self._timestamp = timestamp
        self._eventID = eventID
        self._title = title

    def __str__(self):
        return 'Photo(' + str(map(lambda key: str(key) + '=' +
               str(self.__dict__[key]), self.__dict__.keys())) + ')'

    @property
    def id(self):
        return self._id

    @property
    def filename(self):
        return self._filename

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def filesize(self):
        return self._filesize

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def eventID(self):
        return self._eventID

    @property
    def title(self):
        return self._title


class _ReadOnlySqlite3Database(object):


    def __init__(self, dbFile):
        self._con = sqlite3.connect(dbFile)
        self._con.row_factory = sqlite3.Row

    def _selectOne(self, selectSQL, rowMapper):
        return self._selectMany(selectSQL, rowMapper)[0]

    def _selectMany(self, selectSQL, rowMapper):
        cursor = self._con.cursor()
        try:
            cursor.execute(selectSQL)
            return map(rowMapper, cursor.fetchall())
        finally:
            cursor.close()

    def close(self):
        if self._con != None:
            self._con.close()
            self._con = None


class RowMapper:


    @staticmethod
    def version(row):
        return Version(row['schema_version'], row['app_version'],
                       row['user_data'])

    @staticmethod
    def event(row):
        return Event(row['id'], row['name'])

    @staticmethod
    def tag(row):
        return Tag(row['id'], row['name'], row['photo_id_list'])

    @staticmethod
    def photo(row):
        return Photo(row['id'], row['filename'], row['width'], row['height'],
                     row['filesize'], row['timestamp'], row['event_id'])

    @staticmethod
    def photo_with_title(row):
        return Photo(row['id'], row['filename'], row['width'], row['height'],
                     row['filesize'], row['timestamp'], row['event_id'],
                     row['title'])


class ShotwellDB(_ReadOnlySqlite3Database):


    _PHOTO_SQL_NO_TITLE   = 'select id, filename, width, height, filesize,' + \
                            ' timestamp, event_id from PhotoTable'
    _PHOTO_SQL_WITH_TITLE = 'select id, filename, width, height, filesize,' + \
                            ' timestamp, event_id, title from PhotoTable'

    def __init__(self, sqlitePath=os.path.join(os.path.expanduser('~'),
                                               '.shotwell', 'data',
                                               'photo.db')):
        _ReadOnlySqlite3Database.__init__(self, sqlitePath)

    def __str__(self):
        return 'ShotwellDB(' + str(map(lambda key: str(key) + '=' +
               str(self.__dict__[key]), self.__dict__.keys())) + ')'

    def version(self):
        return self._selectOne('select schema_version, app_version,' +
                               ' user_data from VersionTable',
                               RowMapper.version)

    def event(self, id):
        return self._selectOne('select id, name from EventTable where id = ' +
                               str(id), RowMapper.event)

    def events(self):
        return self._selectMany('select id, name from EventTable',
                                RowMapper.event)

    def tag(self, id):
        return self._selectOne('select id, name, photo_id_list from' +
                               ' TagTable where id = ' + str(id),
                               RowMapper.tag)

    def tags(self):
        return self._selectMany('select id, name, photo_id_list from TagTable',
                                RowMapper.tag)

    def photo(self, id):
        if self.version().schemaVersion < 5:
            return self._selectOne(self._PHOTO_SQL_NO_TITLE + ' where id = ' +
                                   str(id), RowMapper.photo)
        else:
            return self._selectOne(self._PHOTO_SQL_WITH_TITLE +
                                   ' where id = ' + str(id),
                                   RowMapper.photo_with_title)

    def photos(self):
        if self.version().schemaVersion < 5:
            return self._selectMany(self._PHOTO_SQL_NO_TITLE, RowMapper.photo)
        else:
            return self._selectMany(self._PHOTO_SQL_WITH_TITLE,
                                    RowMapper.photo_with_title)
