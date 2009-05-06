import soup

import conduit.utils as Utils
import conduit.modules.TomboyModule as TomboyModule

import datetime

class TomboyNoteWrapper(soup.data.DataWrapper):

    wraps = TomboyModule.TomboyNote

    def iter_samples(self):
        #FIXME: This is not very useful
        for f in self.get_files_from_data_dir("*"):
            n = TomboyModule.TomboyNote(Utils.random_string(), Utils.random_string(), xml=None)
            n.set_mtime(datetime.datetime.now())
            n.set_UID(Utils.random_string())
            yield n

    def generate_sample(self):
        pass

