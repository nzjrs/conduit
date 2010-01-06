def N_(message): return message

HINT_BLANK_CANVAS           = -100
HINT_ADD_DATAPROVIDER       = -101
HINT_RIGHT_CLICK_CONFIGURE  = -102

HINT_TEXT = {
    HINT_BLANK_CANVAS:(             N_("What Do You Want to Synchronize?"),
                                    N_("Drag and Drop a Data Provider on the Canvas"),
                                    True),
    HINT_ADD_DATAPROVIDER:(         N_("Synchronization Group Created"),
                                    N_("Add Another Data Provider to the Group to Synchronize it"),
                                    False),
    HINT_RIGHT_CLICK_CONFIGURE:(    N_("You Are Now Ready to Synchronize"),
                                    N_("Right Click on Group for Options"),
                                    False)
}

PRECONFIGIRED_CONDUITS = {
    #source,sinc                            
        #comment
        #twoway
    ("FolderTwoWay","FolderTwoWay"):(
        N_("Synchronize Two Folders"),
        True    ),
    ("FolderTwoWay","BoxDotNetTwoWay"):(
        N_("Backup Folder to Box.net"),
        False   ),
    ("FSpotDbusTwoWay","FlickrTwoWay"):(
        N_("Synchronize Tagged F-Spot Photos to Flickr"),
        False   ),
    ("FileSource","FlickrTwoWay"):(
        N_("Synchronize Photos to Flickr"),
        False   ),
    ("FileSource","FacebookSink"):(
        N_("Upload Photos to Facebook"),
        False   ),
    ("RSSSource","DesktopWallpaperDataProvider"):(
        N_("Synchronize Desktop Wallpaper from a RSS Feed"),
        False   ),
}


