import soup

import conduit.utils as Utils
from conduit.datatypes import Note

class NoteWrapper(soup.data.DataWrapper):

    def iter_samples(self):
        #FIXME: This is not very useful
        for f in self.get_files_from_data_dir("*"):
            n = Note.Note(Utils.random_string(), Utils.random_string())
            n.set_UID(Utils.random_string())
            yield n

    def generate_sample(self):
        pass

