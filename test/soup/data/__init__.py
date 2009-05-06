import os, sys, glob

from conduit.datatypes import DataType, File

from soup.utils.pluginloader import PluginLoader

class DataWrapper(object):
    """
    This class provides a wrapper around some test data.
    """

    requires = []

    @classmethod
    def name(cls):
        return cls.__name__

    def get_data_dir(self):
        return os.path.join(os.path.dirname(__file__),"..","..","python-tests","data")

    def get_files_from_data_dir(self, glob_str):
        """ Yields files that match the glob in the data dir """
        files = []
        for i in glob.glob(os.path.join(self.get_data_dir(),glob_str)):
            if os.path.isfile(i):
                yield os.path.abspath(i)

    def iter_samples(self):
        """ Yield DataType objects containing sample data """
        raise NotImplementedError

    def generate_sample(self):
        """ Generate a single DataType object with random data """
        raise NotImplementedError

    def mutate_sample(self, obj):
        """ Modify a DataType object randomly """
        return obj

    @classmethod
    def get_datatype(cls):
        return cls.wraps

    @classmethod
    def get_compatible_datatypes(cls):
        """ Yields DataType classes that are (probably) compatible with this one

            We can't rely on type converter system to make sane convertablity choices,
            or we'd end up in a situation where we tried to convert a vcard into an mp3
            (vcard to file, but file could convert to mp3. doh).

            Instead we work out convertability by looking 'down class' (we assume there is a
            conversion route from GoogleContact to Contact.

            We also make some bold assumptions about being able to convert to and from files """
        yield cls.get_datatype()

        # Yuck. Assume compatibiliy with File.
        yield File.File

        tovisit = list(cls.get_datatype().__bases__)
        while len(tovisit):
            n = tovisit.pop(0)
            if not issubclass(n, DataType.DataType):
                continue
            if n == File.File:
                continue
            tovisit.extend(n.__bases__)
            yield (cls.get_datatype(), n, cls)

    @classmethod
    def is_compatible(cls, datatype):
        compatible = list(cls.get_compatible_datatypes())
        return datatype in compatible

class _DataLoader(PluginLoader):
    _subclass_ = DataWrapper
    _module_ = "soup.data"
    _path_ = os.path.dirname(__file__)

DataLoader = _DataLoader()

