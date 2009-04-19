import unittest

import modules

class TestSynchronizationPair(BaseTest):

    def __init__(self, source, sink):
        super(TestSynchronizationPair, self).__init__(self)
        self.source = source
        self.sink = sink

    def testDoNothing(self):
        pass

class TestSynchronization(unittest.TestSuite):

    def __init__(self, tests=None):
        """ Generate TestSuite for all module wrapper pairs  """
        tests = []
        for a in modules.all():
            for b in modules.all():
                tests.append(TestSynchronizationPair(a, b))

        super(TestSynchronization, self).__init__(tests)

