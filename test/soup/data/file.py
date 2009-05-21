import soup
import soup.data

import conduit.utils as Utils
from conduit.datatypes import File

class FileWrapper(soup.data.DataWrapper):
    """ Provides access to sample files and generated files """

    wraps = File.File

    def iter_samples(self):
        for f in self.get_files_from_data_dir("*"):
            yield File.File(URI=f)

    def generate_sample(self):
        f = Utils.new_tempfile(Utils.random_string())
        uri = f._get_text_uri()
        f.set_UID(uri)
        f.set_open_URI(uri)
        return f

