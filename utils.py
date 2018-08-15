import datetime
import hashlib
import os
import subprocess
from os.path import splitext

from flask import current_app
from flask_security import current_user

from models import db, Role, Logging, Config, UserLogging


def gcfg():
    _config = Config.query.one()
    if not _config:
        return {"app_name": "ree2bits"}
    return {"app_name": _config.app_name}


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
    print(
        "[LOG][{0}][{1}][u:{2}i:{3}] {4}".format(
            level.upper(), category, user, item, message
        )
    )
    a = UserLogging(
        category=category,
        level=level.upper(),
        message=message,
        item_id=item,
        user_id=user,
    )
    db.session.add(a)
    db.session.commit()


def duration_elapsed_human(seconds):
    print(seconds)
    seconds = round(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    years, days = divmod(days, 365.242199)

    minutes = int(minutes)
    hours = int(hours)
    days = int(days)
    years = int(years)

    if years > 0:
        return "%d y" % years
    elif days > 0:
        return "%d d" % days
    elif hours > 0:
        return "%d h" % hours + "s" * (hours != 1)
    elif minutes > 0:
        return "%d mn" % minutes + "s" * (minutes != 1)
    else:
        return "right now"


def duration_song_human(seconds):
    if seconds is None:
        return "error"
    seconds = float(seconds)
    seconds = seconds
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


def get_waveform(filename):
    binary = current_app.config["AUDIOWAVEFORM_BIN"]
    if not os.path.exists(binary) or not os.path.exists(filename):
        add_log(
            "AUDIOWAVEFORM",
            "ERROR",
            "Filename {0} or binary {1} invalid".format(filename, binary),
        )
        return None

    tmpjson = "{0}.json".format(filename)

    cmd = [
        binary,
        "-i",
        filename,
        "--pixels-per-second",
        "10",
        "-b",
        "8",
        "-o",
        tmpjson,
    ]

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
        json = f.readlines()

    os.unlink(tmpjson)

    if isinstance(json, list):
        json = json[0].rstrip()
    return json


def create_png_waveform(fn_audio, fn_png):
    binary = current_app.config["AUDIOWAVEFORM_BIN"]
    if not os.path.exists(binary) or not os.path.exists(fn_audio):
        add_log(
            "AUDIOWAVEFORM_PNG",
            "ERROR",
            "Filename {0} or binary {1} invalid".format(fn_audio, binary),
        )
        return None

    pngwf = "{0}.png".format(fn_png)
    cmd = [
        binary,
        "-i",
        fn_audio,
        "--width",
        "384",
        "--height",
        "64",
        "--no-axis-labels",
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
        add_log(
            "AUDIOWAVEFORM_PNG", "ERROR", "Process error: {0}".format(process.stderr)
        )
        return None

    return True


def get_hashed_filename(filename):
    f_n, f_e = splitext(filename)

    fs_fname = hashlib.sha256()
    hashed_format = "%s-%s" % (f_n, datetime.datetime.now())
    fs_fname.update(hashed_format.encode("utf-8"))
    fs_fname = fs_fname.hexdigest()

    return fs_fname + f_e
