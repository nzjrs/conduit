
from soup import UnavailableFeature
from soup.utils import progressbar

import sys
import unittest
import cgitb
import traceback


class TestResult(unittest.TestResult):

    def __init__(self, stream, descriptions, verbosity, num_tests=None):
        super(TestResult, self).__init__()
        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.num_tests = num_tests

    def startTest(self, test):
        super(TestResult, self).startTest(test)
        self.report_test_start(test)

    def stopTest(self, test):
        super(TestResult, self).stopTest(test)
        self.report_test_stop(test)

    def addError(self, test, err):
        if isinstance(err, UnavailableFeature):
            self.addSkipped(self, test)
        else:
            super(TestResult, self).addError(test, err)
            self.report_error(test)

    def addFailure(self, test, err):
        super(TestResult, self).addFailure(test, err)
        self.report_failure(test)

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

    def report_finished(self):
        self.stream.writeln()
        self.printErrorList('ERROR', self.errors)
        self.printErrorList('FAIL', self.failures)

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


class VerboseConsoleTextResult(TextTestResult):

    def report_test_start(self, test):
        print test.shortDescription()


class TestRunner(object):

    def __init__(self, stream=sys.stderr, descriptions=0, verbosity=1):
        self.stream = unittest._WritelnDecorator(stream)
        self.descriptions = 0
        self.verbosity = 0

    def make_results(self, tests):
        if self.verbosity > 1:
            klass = VerboseConsoleTextResult
        else:
            klass = SimpleTestResult

        return klass(self.stream, self.descriptions, self.verbosity, num_tests=tests.countTestCases())

    def run(self, tests):
        result = self.make_results(tests)
        result.report_starting()
        tests.run(result)
        result.report_finished()
        return result
