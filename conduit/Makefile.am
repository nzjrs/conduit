SUBDIRS = datatypes dataproviders modules gtkui utils platform vfs

conduitbindir = $(bindir)
conduitbin_SCRIPTS = \
	conduit

conduitdir = $(pythondir)/conduit
conduit_PYTHON = \
	Conduit.py \
	Configurator.py \
	Conflict.py \
	Database.py \
	DBus.py \
	defs.py \
	DeltaProvider.py \
	Exceptions.py \
	Globals.py \
	__init__.py \
	Knowledge.py \
	Logging.py \
	libconduit.py \
	Main.py \
	MappingDB.py \
	Module.py \
	ModuleWrapper.py \
	Settings.py \
	Synchronization.py \
	SyncSet.py \
	TypeConverter.py \
	Web.py \
	XMLSerialization.py
	
CLEANFILES = \
	defs.py \
	$(BUILT_SOURCES)
	
DISTCLEANFILES = \
	$(CLEANFILES)
	
EXTRA_DIST = \
	defs.py.in \
	conduit

clean-local:
	rm -rf *.pyc *.pyo
