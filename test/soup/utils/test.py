
import soup
from soup.utils import progressbar

import sys
import unittest
import cgitb
import traceback
import time

# FIXME: These only need to be here because i'm mixing unittest tweaks with conduit helpers
import os
import conduit
import conduit.utils as Utils
import conduit.MappingDB as MappingDB
import conduit.Module as Module
import conduit.TypeConverter as TypeConverter
import conduit.Synchronization as Synchronization
import conduit.ModuleWrapper as ModuleWrapper
import conduit.Conduit as Conduit
import conduit.Settings as Settings

CHANGE_ADD = 1
CHANGE_REPLACE = 2
CHANGE_DELETE = 3


class TestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(TestCase, self).__init__(methodName)
        self.testMethodName = methodName
        self.testMethod = getattr(self, methodName)

    @classmethod
    def name(cls):
        """ Returns the name of the class. We need to override this on generated classes """
        return cls.__name__

    def id(self):
        """ Returns the name of the class and the test this particular instance will run """
        return self.name() + "." + self.testMethodName

    def requires(self):
        """ Yields feature objects that we depend on to run this test, such as an internet connection or python-gpod """
        return []

    def shortDescription(self):
        """ Describe the test that is currently running
            Returns something like TestClass.test_function: Tests how good Conduit is """
        return "%s.%s: %s" % (self.name(), self.testMethodName, super(TestCase, self).shortDescription())

    def setUp(self):
        for feature in self.requires():
            feature.require()

    def setUpSync(self):
        # FIXME: I'd put this in an EnvironmentWrapper, but i need priorities before i can do that :/
        conduit.IS_INSTALLED =              False
        conduit.IS_DEVELOPMENT_VERSION =    True
        conduit.SHARED_DATA_DIR =           os.path.join(soup.get_root(),"data")
        conduit.SHARED_MODULE_DIR =         os.path.join(soup.get_root(),"conduit","modules")
        conduit.FILE_IMPL =                 os.environ.get("CONDUIT_FILE_IMPL","GIO")
        conduit.BROWSER_IMPL =              os.environ.get("CONDUIT_BROWSER_IMPL","system")
        conduit.SETTINGS_IMPL =             os.environ.get("CONDUIT_SETTINGS_IMPL","Python")
        conduit.GLOBALS.settings =          Settings.Settings()

        #Set up our own mapping DB so we dont pollute the global one
        dbFile = os.path.join(os.environ['TEST_DIRECTORY'],Utils.random_string()+".db")
        conduit.GLOBALS.mappingDB = MappingDB.MappingDB(dbFile)

        self.modules = Module.ModuleManager([])
        conduit.GLOBALS.moduleManager = self.modules
        self.modules.load_all(whitelist=None, blacklist=None)

        self.type_converter = conduit.TypeConverter.TypeConverter(self.modules)
        conduit.GLOBALS.typeConverter = self.type_converter
        self.sync_manager = conduit.Synchronization.SyncManager(self.type_converter)
        conduit.GLOBALS.syncManager = self.sync_manager

    def get_dataprovider(self, name):
        wrapper = None
        for dp in self.modules.get_all_modules():
            if dp.classname == name:
                wrapper = self.modules.get_module_wrapper_with_instance(dp.get_key())
        assert wrapper != None
        return wrapper

    def get_dataprovider_factory(self, className, die=True):
        factory = None
        for f in self.model.dataproviderFactories:
            if f.__class__.__name__ == className:
                factory = f
        assert factory != None
        return factory

    def wrap_dataprovider(self, dp):
        wrapper = ModuleWrapper.ModuleWrapper(
                         klass=dp.__class__,
                         initargs=(),
                         category=None
                         )
        wrapper.module = dp
        return wrapper

    def networked_dataprovider(self, dp):
        """
        Dirty evil cludge so we can test networked sync...
        """
        factory = self.get_dataprovider_factory("NetworkServerFactory")
        server = factory.share_dataprovider(dp)
        assert server != None

        conduit = Conduit.Conduit(self.sync_manager)
        time.sleep(1)

        factory = self.get_dataprovider_factory("NetworkClientFactory")
        newdp = factory.dataprovider_create("http://localhost", conduit.uid, server.get_info())
        assert newdp != None
        return self.wrap_dataprovider( newdp() )

    def create_conduit(self):
        return Conduit.Conduit(self.sync_manager)

    def create_syncset(self):
        return SyncSet.SyncSet(
            moduleManager=self.modules,
            syncManager=self.sync_manager
        )


#
# Custom exceptions
#

class TestSkipped(Exception):
    """ Indicate a test was intentionally skipped rather than failed """


class UnavailableFeature(Exception):
    """ A feature required for this test was unavailable """


#
# 'Features'
# Some tests need things that might not be available, like python gpod, so provide an interface
# to fail gracefully.
#

class Feature(object):

    def __init__(self):
        self._cached = None

    def probe(self):
        raise NotImplementedError

    def available(self):
        if self._cached == None:
            self._cached = self.probe()
        return self._cached

    def require(self):
        if not self.available():
            raise UnavailableFeature(self)

    def name(self):
        return self.__name__

    def __str__(self):
        return self.name()

class Package(Feature):

    def __init__(self, *args):
        super(Package, self).__init__()
        self.packages = args

    def probe(self):
        for p in self.packages:
            try:
                __import__(p)
            except:
                return False
        return True

    def name(self):
        return "python dependencies ('%s')" % ", ".join(self.packages)

class _HumanInteractivity(Feature):

    def probe(self):
        try:
            return os.environ["CONDUIT_INTERACTIVE"] == "TRUE"
        except:
            return False

    def name(self):
        return "human button masher"

HumanInteractivity = _HumanInteractivity()


class _Online(Feature):

    def probe(self):
        try:
            return os.environ["CONDUIT_ONLINE"] == "TRUE"
        except:
            return False

    def name(self):
        return "internet access"

Online = _Online()


#
# Custom test loader
#

class TestLoader(unittest.TestLoader):

    def __init__(self, include=None, exclude=None):
        self.include = include or []
        self.exclude = exclude or []

    def _flatten(self, tests):
        if isinstance(tests, unittest.TestSuite):
            for test in tests:
                for subtest in self._flatten(test):
                    yield subtest
        else:
            yield tests

    def loadTestsFromModule(self, module):
        for test in self._flatten(super(TestLoader, self).loadTestsFromModule(module)):
            if len(self.include) > 0:
                is_included = False
                for i in self.include:
                    if i in test.id():
                        is_included = True
                if not is_included:
                    continue
            if len(self.exclude) > 0:
                is_excluded = False
                for x in self.exclude:
                    if x in test.id():
                        is_excluded = True
                if is_excluded:
                    continue
            yield test

    def loadTestsFromMain(self):
        """ Load all tests that can be found starting from __main__ """
        return self.loadTestsFromModule(__import__('__main__'))


class TestResult(unittest.TestResult):

    def __init__(self, stream, descriptions, verbosity, num_tests=None):
        super(TestResult, self).__init__()
        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.num_tests = num_tests
        self.unsupported = {}

    def startTest(self, test):
        super(TestResult, self).startTest(test)
        self.report_test_start(test)

    def stopTest(self, test):
        super(TestResult, self).stopTest(test)
        self.report_test_stop(test)

    def addError(self, test, err):
        if isinstance(err[1], UnavailableFeature):
            self.addUnsupported(test, err[1].args[0])
        else:
            super(TestResult, self).addError(test, err)
            self.report_error(test)

    def addFailure(self, test, err):
        super(TestResult, self).addFailure(test, err)
        self.report_failure(test)

    def addUnsupported(self, test, feature):
        self.unsupported.setdefault(str(feature), 0)
        self.unsupported[str(feature)] += 1
        self.report_unsupported(test, feature)

    def addSkipped(self, test):
        self.report_skipped(test)

    def addSuccess(self, test):
        super(TestResult, self).addSuccess(test)
        self.report_success(test)

    def _exc_info_to_string(self, err, test):
        """Converts a sys.exc_info()-style tuple of values into a string."""
        exctype, value, tb = err
        # Skip test runner traceback levels
        while tb and self._is_relevant_tb_level(tb):
            tb = tb.tb_next
            if exctype is test.failureException:
                # Skip assert*() traceback levels
                length = self._count_relevant_tb_levels(tb)
                return ''.join(traceback.format_exception(exctype, value, tb, length))
        return cgitb.text((exctype, value, tb))

    # FIXME: Maybe these should be callbacks?

    def report_starting(self):
        pass

    def report_test_start(self, test):
        pass

    def report_test_stop(self, test):
        pass

    def report_error(self, test):
        pass

    def report_failure(self, test):
        pass

    def report_unsupported(self, test, feature):
        pass

    def report_skipped(self, test):
        pass

    def report_success(self, test):
        pass

    def report_finished(self):
        pass


class TextTestResult(TestResult):

    seperator1 = '=' * 70
    seperator2 = '-' * 70

    def getDescription(self, test):
        return test.shortDescription()

    def report_finished(self, timeTaken):
        self.stream.writeln()
        self.printErrorList('ERROR', self.errors)
        self.printErrorList('FAIL', self.failures)
        self.stream.writeln(self.seperator2)

        run = self.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        self.stream.writeln()

        if not self.wasSuccessful():
            self.stream.write("FAILED (")
            failed, errored = map(len, (self.failures, self.errors))
            if failed:
                self.stream.write("failures=%d" % failed)
            if errored:
                if failed: self.stream.write(", ")
                self.stream.write("errors=%d" % errored)
            self.stream.writeln(")")
        else:
            self.stream.writeln("OK")

        if len(self.unsupported) > 0:
            for feature, count in self.unsupported.iteritems():
                self.stream.writeln("%s not available, %d tests skipped" % (feature, count))

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.seperator1)
            self.stream.writeln("%s: %s" % (flavour, self.getDescription(test)))
            self.stream.writeln(self.seperator2)
            self.stream.writeln("%s" % err)


class SimpleTestResult(TextTestResult):

    def report_starting(self):
        self.pb = progressbar.ProgressBar()
        self.pb.max = self.num_tests

    def report_test_start(self, test):
        self.pb.update(self.pb.cur + 1)

    def report_finished(self, timetaken):
        self.pb.finish()
        super(SimpleTestResult, self).report_finished(timetaken)


class VerboseConsoleTextResult(TextTestResult):

    def report_test_start(self, test):
        print test.shortDescription()


class TestRunner(object):

    def __init__(self, opts, stream=sys.stderr, descriptions=0, verbosity=1):
        self.stream = unittest._WritelnDecorator(stream)
        self.descriptions = 0
        self.verbosity = 0

    def make_results(self, tests):
        if self.verbosity > 1:
            klass = VerboseConsoleTextResult
        else:
            klass = SimpleTestResult

        return klass(self.stream, self.descriptions, self.verbosity, num_tests=tests.countTestCases())

    def iter_tests(self, tests):
        if isinstance(tests, unittest.TestSuite):
            for test in tests:
                for subtest in self.iter_tests(test):
                    yield subtest
        else:
            yield tests

    def run(self, tests):
        result = self.make_results(tests)
        result.report_starting()

        start_time = time.time()

        for t in self.iter_tests(tests):
            tr = soup.env.EnvironmentLoader.decorate_test(t.run)
            tr(result)

        time_taken = time.time() - start_time

        result.report_finished(time_taken)
        return result

