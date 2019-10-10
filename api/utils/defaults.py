# This is the central point of various defaults used in reel2bits
# There should not be edited, they are just here to eases development


class Reel2bitsDefaults(object):
    # Warning: The order can't change, also a licence cannot be renamed to another one (except typo)
    known_licences = {
        0: {"name": "Not Specified", "id": 0, "link": "", "icon": ""},
        1: {
            "name": "CC Attribution",
            "id": 1,
            "link": "https://creativecommons.org/licenses/by/4.0/",
            "icon": "creative-commons",
        },
        2: {
            "name": "CC Attribution Share Alike",
            "id": 2,
            "link": "https://creativecommons.org/licenses/by-sa/4.0",
            "icon": "creative-commons",
        },
        3: {
            "name": "CC Attribution No Derivatives",
            "id": 3,
            "link": "https://creativecommons.org/licenses/by-nd/4.0",
            "icon": "creative-commons",
        },
        4: {
            "name": "CC Attribution Non Commercial",
            "id": 4,
            "link": "https://creativecommons.org/licenses/by-nc/4.0",
            "icon": "creative-commons",
        },
        5: {
            "name": "CC Attribution Non Commercial - Share Alike",
            "id": 5,
            "link": "https://creativecommons.org/licenses/by-nc-sa/4.0",
            "icon": "creative-commons",
        },
        6: {
            "name": "CC Attribution Non Commercial - No Derivatives",
            "id": 6,
            "link": "https://creativecommons.org/licenses/by-nc-nd/4.0",
            "icon": "creative-commons",
        },
        7: {"name": "Public Domain Dedication", "id": 7, "link": "", "icon": ""},
    }

    # http://www.matisse.net/bitcalc/
    # Every size are in bytes
    # Default is going to be 1 gb
    user_quotas_default = 134217728
    user_quotas_available = [
        {"bytes": 134217728},  # 1 gb
        {"bytes": 671088640},  # 5 gb
        {"bytes": 2684354560},  # 20 gb
        {"bytes": 6710886400},  # 50 gb
    ]

    # 100 megabytes
    track_size_limit = 104857600

    # 2MB
    artwork_size_limit = 2000000
    avatar_size_limit = artwork_size_limit

    artwork_extensions_allowed = tuple("jpg jpe jpeg png gif JPG JPE JPEG PNG GIF".split())
    avatar_extensions_allowed = artwork_extensions_allowed
