#!/usr/bin/env python

import sys
import getopt
import os
import dbus, dbus.glib

try:
    import libconduit
except ImportError:
    import conduit.libconduit as libconduit

def main(useGui, quitWhenFinished, exportFile, startConduit):
    app = libconduit.ConduitApplicationWrapper(
                            conduitWrapperKlass=libconduit.ConduitWrapper,
                            addToGui=useGui,
                            store=False,
                            debug=False
                            )
    if not app.connect_to_conduit(startConduit):
        print "Conduit not running"
        return 

    print "Available Dataproviders"
    for dp in app.get_dataproviders():
        print " * ",dp

    #Use libconduit to create a file sync/exporter conduit
    cond = app.build_conduit("TestSink")
    #Add file to sync/export
    cond.add_uri(exportFile)
    #Sync all file sync/exporter conduits
    app.sync()

    #Call a raw dbus message on the underlying application
    if quitWhenFinished:
        app.get_application().Quit()

def usage(me):
    usage = "%s --export=FILE\n" + \
            "Options:\n" + \
            "\t--gui\tShow the conduit (syncset) in the GUI\n" + \
            "\t--quit\tClose conduit when finished"
    print usage % me
    sys.exit(1)

if __name__ == '__main__':
    me = sys.argv[0]
    try:
        opts, args = getopt.getopt(sys.argv[1:], "e:gqs", ["export=", "gui", "quit", "start"])
    except getopt.GetoptError:
        usage(me)

    start = False
    quit = False
    gui = False
    export = None
    for o, a in opts:
        if o in ("-g", "--gui"):
            gui = True
        if o in ("-q", "--quit"):
            quit = True
        if o in ("-s", "--start"):
            start = True
        if o in ("-e", "--export"):
            export = os.path.abspath(a)
        
    if export and os.path.exists(export):
        main(
            useGui=gui,
            quitWhenFinished=quit,
            exportFile=export,
            startConduit=start)
    else:
        usage(me)
