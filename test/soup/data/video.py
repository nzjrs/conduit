import soup

from conduit.datatypes import Video

import datetime

class VideoWrapper(soup.data.DataWrapper):

    wraps = Video.Video

    def iter_samples(self):
        for f in self.get_files_from_data_dir("*.mpg"):
            a = Video.Video(URI=f)
            a.set_mtime(datetime.datetime.now())
            a.set_UID(f)
            yield a

    def generate_sample(self):
        pass

