from common import *

import traceback
import gobject
import threading

import gtk
gtk.gdk.threads_init()

import conduit.datatypes.File as File
import conduit.datatypes.Video as Video
import conduit.datatypes.Audio as Audio
import conduit.modules.iPodModule.iPodModule as iPodModule
import conduit.utils as Utils
import conduit.Exceptions as Exceptions

finished()

test = SimpleTest()
tc = test.type_converter

ok("Video Conversion exists", tc.conversion_exists("file","file/video") == True, False)
ok("Audio Conversion exists", tc.conversion_exists("file","file/audio") == True, False)

VIDEO_ENCODINGS = Video.PRESET_ENCODINGS
VIDEO_ENCODINGS.update(iPodModule.IPOD_VIDEO_ENCODINGS)

TEST = (
#name.list          #encodings of source files to test              #available encodings of dest file
("video",           ('divx', 'flv', 'ogg', 'mp4_x264', 'mp4_xvid'), VIDEO_ENCODINGS),
("audio",           ('ogg','mp3'),                                  Audio.PRESET_ENCODINGS      ),
)
mainloop = gobject.MainLoop()

def convert():    
    for name, test_encodings, all_encodings in TEST:
        files = get_external_resources(name)
        for description,uri in files.items():
            f = File.File(uri)
            exists = f.exists()
            ok("%s: File %s exists" % (name,uri), exists, False)
            if exists:
                for encoding in test_encodings:
                    args = all_encodings[encoding]
                    
                    to_type = "file/%s?%s" % (name,Utils.encode_conversion_args(args))
                    try:
                        newdata = tc.convert("file",to_type, f)
                        success = newdata != None and newdata.exists()
                    except: 
                        success = False

                    ok("%s: Conversion of %s -> %s" % (name,description,encoding), success, False)

    gobject.idle_add(mainloop.quit)

def idle_cb():
    # We must run the conversion tests in a thread because the GStreamer 
    # conversion uses Locks internally which blocks the main loop
    threading.Thread(target=convert).start()
    return False

gobject.idle_add(idle_cb)
mainloop.run()

test.finished()
finished()

