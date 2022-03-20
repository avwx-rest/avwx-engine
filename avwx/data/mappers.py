"""
Type mappings
"""

# Runway surface type matching with counts (2020-06)
# Uniques with < 10 occurrences omitted
SURFACE_TYPES = {
    "asphalt": (
        "asp",  # 10826
        "asph",  # 1522
        "asph-g",  # 631
        "asph/ conc",  # 338
        "asphalt",  # 301
        "asph-f",  # 235
        "asph-p",  # 127
        "bit",  # 87
        "asph-turf",  # 75
        "asph-conc",  # 65
        "b",  # 55
        "asph-e",  # 45
        "paved",  # 33
        "asph-grvl",  # 25
        "asfalt",  # 17
        "asph-conc-g",  # 14
        "asph-dirt",  # 14
        "asph-turf-f",  # 14
        "asph-turf-g",  # 14
    ),
    "turf": (
        "turf",  # 7809
        "grs",  # 1701
        "turf-g",  # 1016
        "grass",  # 781
        "turf-f",  # 495
        "g",  # 449
        "grass / sod",  # 232
        "turf-p",  # 131
        "turf-dirt",  # 77
        "turf-grvl",  # 73
        "grassed brown clay",  # 42
        "turf-grvl-f",  # 31
        "grassed red clay",  # 29
        "grassed brown silt clay",  # 20
        "turf-grvl-g",  # 19
        "turf-dirt-f",  # 17
        "turf-grvl-p",  # 17
        "turf-e",  # 14
        "turf-dirt-p",  # 14
        "turf/grass",  # 13
        "grass/gravel",  # 11
        "grassed black silt clay",  # 11
        "grassed black clay",  # 10
        "grassed brown gravel",  # 10
    ),
    "concrete": (
        "conc",  # 3078
        "con",  # 2283
        "pem",  # 335
        "conc-g",  # 236
        "c",  # 151
        "concrete",  # 148
        "conc-turf",  # 42
        "conc-f",  # 14
        "conc-e",  # 12
    ),
    "gravel": (
        "gre",  # 1563
        "gvl",  # 342
        "gravel",  # 340
        "grvl",  # 321
        "grvl-g",  # 78
        "grvl-f",  # 47
        "gravel-g",  # 41
        "grv",  # 35
        "grvl-dirt",  # 32
        "grvl-p",  # 30
        "cop",  # 29
        "crushed rock",  # 22
        "gravel-p",  # 20
        "grvl-trtd",  # 19
        "com",  # 18
        "grv/grass",  # 17
        "gravel-f",  # 16
        "coral",  # 16
        "treated gravel",  # 16
        "grvl-dirt-p",  # 15
        "grvl-dirt-f",  # 13
        "mac",  # 12
        "gravel / cinders / crushed rock / coral/shells / slag",  # 10
    ),
    None: (
        "unk",
        "",
        "per",
    ),  # 689  # 319  # 30
    "water": (
        "water",
        "water-e",
    ),  # 686  # 60
    "dirt": (
        "dirt",  # 532
        "x",  # 436
        "n",  # 354
        "s",  # 131
        "l",  # 54
        "dirt-f",  # 48
        "ter",  # 36
        "dirt-g",  # 35
        "dirt-p",  # 29
        "earth",  # 24
        "ground",  # 22
        "cla",  # 20
        "clay",  # 15
        "trtd-dirt",  # 14
        "trtd",  # 12
        "graded earth",  # 11
    ),
    "constructed": (
        "mats",  # 82
        "met",  # 69
        "wood",  # 62
        "pad",  # 36
        "roof-top",  # 25
        "pierced steel planking / landing mats / membranes",  # 22
        "psp",  # 14
    ),
    "sand": (
        "sand",
        "san",
    ),  # 20  # 20
    "ice": ("ice",),  # 13
    "snow": (
        "turf/snow",
        "snow",
    ),  # 12
}


# Replace malformed UTF characters
FILE_REPLACE = {
    "Æ\x8f": "Ə",
    "Ã\x81": "Á",
    "Ã„": "Ä",
    "Ã…": "Å",
    "Ã‚": "Â",
    "Ãƒ": "Ã",
    "Ã¡": "á",
    "áº£": "ả",
    "áº¥": "ấ",
    "Ã£": "ã",
    "Ã¢": "â",
    "Äƒ": "ă",
    "Ã¤": "ä",
    "Ã¥": "å",
    "áº©": "ẩ",
    "Ä…": "ą",
    "Ä\x81": "ā",
    "áºµ": "ẵ",
    "Ã¦": "æ",
    "ÃŸ": "ß",
    "ÄŒ": "Č",
    "Ã‡": "Ç",
    "Ä†": "Č",
    "Ã§": "ç",
    "Ä‡": "ć",
    "Ä\x8d": "č",
    "ÄŽ": "Ď",
    "Ä\x90": "Đ",
    "Ä\x8f": "ď",
    "Ä‘": "đ",
    "Ã‰": "É",
    "Ã©": "é",
    "È©": "ę",
    "Ä™": "ę",
    "Ã¨": "è",
    "Ã«": "ë",
    "Ä“": "ē",
    "Ä—": "ė",
    "Ãª": "ê",
    "Ä›": "ě",
    "É™": "ə",
    "áº¿": "ế",
    "ÄŸ": "ğ",
    "Ä¡": "ġ",
    "Ä£": "ģ",
    "Ä°": "İ",
    "ÃŽ": "Î",
    "Ã\x8d": "Í",
    "Ã¯": "ï",
    "Ã¬": "ì",
    "Ã­č": "í",
    "Ä±": "ı",
    "Ã®": "î",
    "Ä«": "ī",
    "Ä¯": "į",
    "Ã\xad": "í",
    "Ä·": "ķ",
    "Å\x81": "Ł",
    "Å‚": "ł",
    "Ä¾": "ľ",
    "Ã‘": "Ñ",
    "Ã±": "ñ",
    "Å„": "ń",
    "Åˆ": "ň",
    "Ä¼": "ņ",
    "Å†": "ņ",
    "Ã–": "Ö",
    "ÅŒ": "Ō",
    "Ã”": "Ô",
    "Ã“": "Ó",
    "Ã˜": "Ø",
    "Å\x90": "Ő",
    "Ãµ": "õ",
    "Ã°": "ð",
    "Ã²": "ò",
    "Ã¶": "ö",
    "Ã³": "ó",
    "á»“": "ồ",
    "á»‘": "ố",
    "á»™": "ộ",
    "Ã´": "ố",
    "Æ¡": "ơ",
    "Å‘": "ő",
    "Ã¸": "ø",
    "Å\x8d": "ō",
    "Å\x8f": "ŏ",
    "Ãž": "Þ",
    "Å˜": "Ř",
    "Å™": "ř",
    "Å ": "Š",
    "Åš": "Ś",
    "Åž": "Ş",
    "Å›": "ś",
    "Å¡": "š",
    "È™": "ș",
    "ÅŸ": "ș",
    "Å\x9d": "ŝ",
    "È›": "ț",
    "Å¥": "ť",
    "Å£": "ț",
    "Ãœ": "Ü",
    "Ãš": "Ú",
    "Ã¼": "ü",
    "Ãº": "ú",
    "Å«": "ū",
    "Å¯": "ů",
    "Ã»": "û",
    "Å³": "ų",
    "á»±": "ự",
    "Ã½": "ý",
    "Å½": "Ž",
    "Å»": "Ż",
    "Åº": "ź",
    "Å¼": "ż",
    "Å¾": "ž",
    "Â¡": "¡",
    "â€“": "–",
    "â€™": "'",
    "â€ž": "„",
    "â€œ": "“",
    "â€\x9d": "”",
    # Key for another replacement
    "Ã†": "Æ",
    # In-place character
    "Â°": "°",
    "Âº": "º",
    # Last because too broad
    "Ã ": "à",
}
