import soup

from conduit.datatypes import Audio

import datetime

class MusicWrapper(soup.data.DataWrapper):

    wraps = Audio.Audio

    def iter_samples(self):
        for f in self.get_files_from_data_dir("*.mp3"):
            a = Audio.Audio(URI=f)
            a.set_mtime(datetime.datetime.now())
            a.set_UID(f)
            yield a

    def generate_sample(self):
        pass

