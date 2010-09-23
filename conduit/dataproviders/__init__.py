import DataProviderCategory

def N_(message): return message

#Default Categories for the DataProviders
CATEGORY_FILES = DataProviderCategory.DataProviderCategory(N_("Files and Folders"), "computer")
CATEGORY_NOTES = DataProviderCategory.DataProviderCategory(N_("Notes"), "note")
CATEGORY_PHOTOS = DataProviderCategory.DataProviderCategory(N_("Photos"), "image-x-generic")
CATEGORY_OFFICE = DataProviderCategory.DataProviderCategory(N_("Office"), "applications-office")
CATEGORY_SETTINGS = DataProviderCategory.DataProviderCategory(N_("Settings"), "applications-system")
CATEGORY_MISC = DataProviderCategory.DataProviderCategory(N_("Miscellaneous"), "applications-accessories")
CATEGORY_MEDIA = DataProviderCategory.DataProviderCategory(N_("Media"), "applications-multimedia")
CATEGORY_BOOKMARKS = DataProviderCategory.DataProviderCategory(N_("Bookmarks"), "user-bookmarks")
CATEGORY_TEST = DataProviderCategory.DataProviderCategory(N_("Test"))
