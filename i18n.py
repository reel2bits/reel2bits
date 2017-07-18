#!/usr/bin/env python
import re
import configparser
import pprint
import os

# START OF CONFIG
"""
Examples for each regexp match:
1.

2.
"""
RES = {
    ".tmpl": re.compile(r"{{\s*\.i18n\.Tr\s+\"(\w*)\.([a-zA-Z_-]*)\"\s*}}"),
    ".go": re.compile(r"ctx\.Tr\(\"(\w*)\.(.*)\"")
}
INI_PARSE = [
    "conf/locale/locale_en-US.ini",
#    "conf/locale/locale_fr-FR.ini",
]
DIRS_SEARCH = [
    "cmd",
    "models",
    "routers",
    "setting",
    "stuff",
    "templates",
]
EXT_ALLOWED = [".go", ".tmpl"]
# END OF CONFIG

# Global variables
"""
[{filename, obj},]
"""
ini_parsed = []

"""
[{ini, filename, section, option, kind},]
"""
unknown = []

# 1. Parse ini file
print("== Parsing {num} INI local files".format(num=len(INI_PARSE)))
for i in INI_PARSE:
    a = configparser.ConfigParser()
    a.read(i)
    ini_parsed.append({'filename': i, 'obj': a})
    print("= {filename}".format(filename=i))

print("")

def compare_inis(match, fname):
    for i in ini_parsed:
        try:
            kv = i['obj'].get(match[0], match[1])
        except configparser.NoOptionError:
            unknown.append({'ini': i['filename'], 'filename': fname, 'section': match[0], 'option': match[1], 'kind': 'option'})
        except configparser.NoSectionError:
            unknown.append({'ini': i['filename'], 'filename': fname, 'section': match[0], 'option': match[1], 'kind': 'section'})

def parse_file(path, fname, ext):
    filename = os.path.join(path, fname)
    print("= Parsing {filename}".format(filename=filename))
    with open(filename, 'r') as f:
        for line in f:
            match = RES[ext].findall(line)
            if match and len(match) >= 1:
                for m in match:
                    compare_inis(m, filename)

# 2. Parse each dirs - walking sub
for directory in DIRS_SEARCH:
    for root, dirs, files in os.walk(directory):
        for fname in files:
            ext = os.path.splitext(fname)[1]
            if ext in EXT_ALLOWED:
                parse_file(root, fname, ext)

# 3. Show non-matched
print("")
if len(unknown) <= 0:
    print("= No unmatched i18n strings detected")
else:
    print("= Unmatched strings:")
    for u in unknown:
        print("From file '{filename}' with ini locale '{ini}', missing [{section}] {option}".format(filename=u['filename'], ini=u['ini'], section=u['section'], option=u['option']))
