
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
        coverage.start()

    def finalize_environment(self):
        coverage.stop()
        modules = glob("conduit/*.py") + glob("conduit/*/*.py") + glob("conduit/*/*/*.py")
        coverage.report(modules, ignore_errors=1, show_missing=0)
        coverage.erase()

