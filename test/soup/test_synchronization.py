import soup

def make_testcase(src, snk):
    class TestSynchronization(soup.TestCase):
        source = src
        sink = snk

        def testDoNothing(self):
            pass

    return TestSynchronization


from soup.modules import folder
TestSynchronizationFolderFolder = make_testcase(folder.FolderWrapper, folder.FolderWrapper)

if __name__ == "__main__":
    import unittest
    unittest.main()
