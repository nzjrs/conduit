import os, sys, glob

class DataWrapper(object):
    """
    This class provides a wrapper around some test data.
    """

    def get_data_dir(self):
        return os.path.join(os.path.dirname(__file__),"..","..","python-tests","data")

    def get_files_from_data_dir(self, glob_str):
        """ Yields files that match the glob in the data dir """
        files = []
        for i in glob.glob(os.path.join(self.get_data_dir(),glob_str)):
            yield os.path.abspath(i)

    def get_all(self):
        raise NotImplementedError

