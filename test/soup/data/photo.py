import soup

from conduit.datatypes import Photo

class PhotoWrapper(soup.data.DataWrapper):

    wraps = Photo.Photo

    def iter_samples(self):
        for f in self.get_files_from_data_dir("*.png"):
            p = Photo.Photo(URI=f)
            p.set_UID(p._get_text_uri())
            yield p

    def generate_sample(self):
        pass

