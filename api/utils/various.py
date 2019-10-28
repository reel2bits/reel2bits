import datetime
import hashlib
import os
import subprocess
from os.path import splitext
import random
import string
import json

from flask import current_app
from flask_security import current_user

from models import db, Role, Logging, UserLogging


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        rv["status"] = "error"
        rv["code"] = self.status_code
        return rv


def is_admin():
    adm = Role.query.filter(Role.name == "admin").first()
    if not current_user or not current_user.is_authenticated or not adm:
        return False
    if adm in current_user.roles:
        return True
    return False


def add_log(category, level, message):
    if not category or not level or not message:
        print("!! Fatal error in add_log() one of three variables not set")
    print("[LOG][{0}][{1}] {2}".format(level.upper(), category, message))
    a = Logging(category=category, level=level.upper(), message=message)
    db.session.add(a)
    db.session.commit()


# categories used, they are used to map the item_id to the right model
# - sounds
# - albums
# - user
# - global
def add_user_log(item, user, category, level, message):
    if not category or not level or not message or not item:
        print("!! Fatal error in add_user_log() one of three variables not set")
    print("[LOG][{0}][{1}][u:{2}i:{3}] {4}".format(level.upper(), category, user, item, message))
    a = UserLogging(category=category, level=level.upper(), message=message, item_id=item, user_id=user)
    db.session.add(a)
    db.session.commit()


def duration_human(seconds):
    if seconds is None:
        return "error"
    seconds = float(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    years, days = divmod(days, 365.242199)

    minutes = int(minutes)
    hours = int(hours)
    days = int(days)
    years = int(years)

    if years > 0:
        return "%d year" % years + "s" * (years != 1)
    elif days > 0:
        return "%d day" % days + "s" * (days != 1)
    elif hours > 0:
        return "%d hour" % hours + "s" * (hours != 1)
    elif minutes > 0:
        return "%d mn" % minutes + "s" * (minutes != 1)
    else:
        return "%.2f sec" % seconds + "s" * (seconds != 1)


# Pixels per seconds, the higher, the more points in the waveform
# the more the waveform is "big in size"
def determine_pps(duration):
    # duration is less than 1 sec
    if duration < 1:
        pps = int(duration * 1000 * 4)
    # duration is less than 30sec
    elif 1 < duration <= 60 / 2:
        pps = 1000
    # duration is more than 30sec but less than 2min
    elif 60 / 2 < duration <= 2 * 60:
        pps = 20
    # duration is more than 2min but less than 30min
    elif 2 * 60 < duration <= 30 * 60:
        pps = 10
    # everything else
    else:
        pps = 1
    print(f"duration: {duration}, pps: {pps}")
    # just in case, cap the PPS to a max of 9999
    return pps if pps < 10000 else 9999


def generate_audio_dat_file(filename, duration):
    binary = current_app.config["AUDIOWAVEFORM_BIN"]
    if not os.path.exists(binary) or not os.path.exists(filename):
        add_log("AUDIOWAVEFORM", "ERROR", "Filename {0} or binary {1} invalid".format(filename, binary))
        return None

    fname, _ = splitext(filename)

    audio_dat = "{0}.dat".format(fname)

    # pixels-per-second is needed here or it will be ignored in the json waveform generation
    pps = determine_pps(duration)
    cmd = [binary, "-i", filename, "-o", audio_dat, "--pixels-per-second", str(pps), "-b", "8"]

    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not process:
            add_log("AUDIOWAVEFORM_DAT", "ERROR", "Subprocess returned None")
            return None
    except subprocess.CalledProcessError as e:
        add_log("AUDIOWAVEFORM_DAT", "ERROR", "Process error: {0}".format(e))
        return None

    print("- Command ran with: {0}".format(process.args))

    if process.stderr.startswith(b"Can't generate"):
        add_log("AUDIOWAVEFORM_DAT", "ERROR", "Process error: {0}".format(process.stderr))
        return None

    return audio_dat


def get_waveform(filename, duration):
    binary = current_app.config["AUDIOWAVEFORM_BIN"]
    if not os.path.exists(binary) or not os.path.exists(filename):
        add_log("AUDIOWAVEFORM", "ERROR", "Filename {0} or binary {1} invalid".format(filename, binary))
        return None

    fname, _ = splitext(filename)

    tmpjson = "{0}.json".format(fname)

    # pixels-persecond is same value as in generate_audio_dat_file
    pps = determine_pps(duration)
    cmd = [binary, "-i", filename, "--pixels-per-second", str(pps), "-b", "8", "-o", tmpjson]

    """
    Failed: Can't generate "xxx" from "xxx"
    OK:
    Input file: piano2.wav
    Frames: 302712
    Sample rate: 48000 Hz
    Channels: 2
    Format: 0x10002
    Sections: 1
    Seekable: yes
    Generating waveform data...
    Samples per pixel: 4800
    Input channels: 2
    Done: 100%
    Read 302712 frames
    Generated 64 points
    Writing output file: some-file.json
    """

    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not process:
            add_log("AUDIOWAVEFORM", "ERROR", "Subprocess returned None")
            return None
    except subprocess.CalledProcessError as e:
        add_log("AUDIOWAVEFORM", "ERROR", "Process error: {0}".format(e))
        return None

    print("- Command ran with: {0}".format(process.args))

    if process.stderr.startswith(b"Can't generate"):
        add_log("AUDIOWAVEFORM", "ERROR", "Process error: {0}".format(process.stderr))
        return None

    with open(tmpjson, "r") as f:
        waveform_json = f.readlines()

    os.unlink(tmpjson)

    if isinstance(waveform_json, list):
        waveform_json = waveform_json[0].rstrip()

    waveform_json = json.loads(waveform_json)

    # normalize the peak datas
    data = waveform_json["data"]
    # number of decimals to use when rounding the peak value
    digits = 2
    max_val = float(max(data))
    new_data = []
    for x in data:
        new_data.append(round(x / max_val, digits))
    waveform_json["data"] = new_data

    return json.dumps(waveform_json)


def create_png_waveform(fn_audio, fn_png):
    binary = current_app.config["AUDIOWAVEFORM_BIN"]
    if not os.path.exists(binary) or not os.path.exists(fn_audio):
        add_log("AUDIOWAVEFORM_PNG", "ERROR", "Filename {0} or binary {1} invalid".format(fn_audio, binary))
        return None

    fname, _ = splitext(fn_png)

    pngwf = "{0}.png".format(fname)

    cmd = [
        binary,
        "-i",
        fn_audio,
        "--width",
        "384",
        "--height",
        "64",
        "--no-axis-labels",
        "--background-color",
        "FFFFFF00",
        "-o",
        pngwf,
    ]

    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not process:
            add_log("AUDIOWAVEFORM_PNG", "ERROR", "Subprocess returned None")
            return None
    except subprocess.CalledProcessError as e:
        add_log("AUDIOWAVEFORM_PNG", "ERROR", "Process error: {0}".format(e))
        return None

    print("- Command ran with: {0}".format(process.args))

    if process.stderr.startswith(b"Can't generate"):
        add_log("AUDIOWAVEFORM_PNG", "ERROR", "Process error: {0}".format(process.stderr))
        return None

    return True


def get_hashed_filename(filename):
    f_n, f_e = splitext(filename)

    fs_fname = hashlib.sha256()
    hashed_format = "%s-%s" % (f_n, datetime.datetime.now())
    fs_fname.update(hashed_format.encode("utf-8"))
    fs_fname = fs_fname.hexdigest()

    return fs_fname + f_e


def generate_random_token():
    t = hashlib.sha256()

    magic_sauce = "".join([random.choice(string.ascii_letters + string.digits) for n in range(250)])
    magic_sauce += str(datetime.datetime.now())

    t.update(magic_sauce.encode("utf-8"))
    return t.hexdigest()[:250]


RESTRICTED_NICKNAMES = [
    ".well-known",
    "~",
    "about",
    "activities",
    "api",
    "auth",
    "check_password",
    "dev",
    "friend-requests",
    "inbox",
    "internal",
    "main",
    "media",
    "nodeinfo",
    "notice",
    "oauth",
    "objects",
    "ostatus_subscribe",
    "pleroma",
    "proxy",
    "push",
    "registration",
    "relay",
    "settings",
    "status",
    "tag",
    "user-search",
    "user_exists",
    "users",
    "web",
    "reel2bits",
    "register",
    "login",
    "oauth-callback",
    "tracks",
    "albums",
    "account",
    "uploads",
    "static",
    "feeds",
]


def forbidden_username(username):
    return username in RESTRICTED_NICKNAMES


def join_url(start, end):
    if end.startswith("http://") or end.startswith("https://"):
        # alread a full URL, joining makes no sense
        return end
    if start.endswith("/") and end.startswith("/"):
        return start + end[1:]

    if not start.endswith("/") and not end.startswith("/"):
        return start + "/" + end

    return start + end
