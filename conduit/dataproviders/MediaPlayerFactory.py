import os.path
import ConfigParser
import logging
log = logging.getLogger("dataproviders.MediaPlayerFactory")

import conduit.utils as Utils
import conduit.utils.UDev as UDev
import conduit.dataproviders.HalFactory as HalFactory

class MediaPlayerFactory(HalFactory.HalFactory):

    #keys to interrogate according to the media-player-info spec
    #                      section,  key name,         store as property
    MPI_ACCESS_PROTOCOL = ("Device", "AccessProtocol", "MPI_ACCESS_PROTOCOL")
    MPI_ICON            = ("Device", "Icon",           "MPI_ICON")
    MPI_KEYS = (MPI_ACCESS_PROTOCOL, MPI_ICON)

    UDEV_SUBSYSTEMS = ("block",)

    #taken from quodlibet
    def __get_mpi_dir(self):
        for d in Utils.get_system_data_dirs():
            path = os.path.join(d, "media-player-info")
            if os.path.isdir(path):
                return path

    #taken from quodlibet
    def __get_mpi_file(self, mplayer_id):
        """
        Returns a SafeConfigParser instance of the mpi file or None.
        MPI files are INI like files usually located in
        /usr/local/media-player-info/*.mpi
        """
        f = os.path.join( self.__get_mpi_dir() , mplayer_id + ".mpi")
        if os.path.isfile(f):
            parser = ConfigParser.SafeConfigParser()
            read = parser.read(f)
            if read: return parser

    def _maybe_new(self, device):
        props = self.gudev.get_device_properties(device)
        sysfs_path = device.get_sysfs_path()
        try:
            mplayer_id = props["ID_MEDIA_PLAYER"]

            #taken from quodlibet
            config = self.__get_mpi_file(mplayer_id)
            if config is not None:
                for (section_name, key_name, prop_name) in self.MPI_KEYS:
                    try:
                        props[prop_name] = config.get(section_name, key_name)
                    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                        pass

            if self.is_interesting(sysfs_path, props):
                self.item_added(sysfs_path, **props)

        except KeyError:
            log.debug("Device not media player (%s)" % props.get("ID_SERIAL", props.get("ID_VENDOR","")))

    def get_mpi_access_protocol(self, props):
        return props.get(self.MPI_ACCESS_PROTOCOL[2], "")

    def get_mpi_icon(self, props, fallback="media-player"):
        return props.get(self.MPI_ICON[2], fallback)

