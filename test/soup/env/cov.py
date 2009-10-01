
import soup

try:
    import coverage
    supports_coverage = True
except:
    supports_coverage = False

from glob import glob


class Coverage(soup.env.EnvironmentWrapper):

    @classmethod
    def enabled(cls, opts):
        if not opts.coverage:
            return False
        #FIXME: Should try importing and fail gracefully if user requests
        # coverage but cant have it
        assert supports_coverage
        return True

    def prepare_environment(self):
        import coverage
        coverage.erase()

    def decorate_test(self, test):
        def _(*args, **kwargs):
            coverage.start()
            test(*args, **kwargs)
            coverage.stop()
        return _

    def finalize_environment(self):
        root = soup.get_root() + '/conduit'
        modules = []
        for i in range(3):
            modules.extend(glob(root + '/*' * i + '.py'))
        coverage.report(modules, ignore_errors=1, show_missing=0)
        coverage.erase()

