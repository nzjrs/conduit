
import soup
from soup.utils import progressbar

import sys
import unittest
import cgitb
import traceback
import time

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
        self.attachments = {}

    def startTest(self, test):
        super(TestResult, self).startTest(test)
        self.report_test_start(test)

    def addAttachment(self, test, name, attachment):
        self.attachments.setdefault(test, [])
        self.attachments[test].append((name, attachment))

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

