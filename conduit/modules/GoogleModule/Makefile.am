SUBDIRS = gdata atom

conduit_handlersdir = $(libdir)/conduit/modules/GoogleModule
conduit_handlers_PYTHON = __init__.py GoogleModule.py

conduit_handlers_DATA = \
	calendar-config.glade

EXTRA_DIST = \
	calendar-config.glade

clean-local:
	rm -rf *.pyc *.pyo
