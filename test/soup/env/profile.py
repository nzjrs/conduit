
import soup

try:
    import cProfile
    import pstats
    supported = True
except ImportError:
    supported = False


class Profile(soup.env.EnvironmentWrapper):

    @classmethod
    def enabled(self, opts):
        if not opts.profile:
            return False
        assert supported, "You need python-profiler to profile the test cases"
        return True

    def decorate_test(self, test):
        def _(*args, **kwargs):
            p = cProfile.Profile()
            res = p.runcall(test, *args, **kwargs)
            #FIXME: Need some way to attach profiling data to report object
            # p.print_stats()
            return res
        return _

