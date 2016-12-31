import os
import random
import re
import string
from functools import wraps

import pytz
from flask import flash
from flask_security import current_user
from markupsafe import Markup
from unidecode import unidecode
from models import db, Apitoken, Role, Logging, Config

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim=u'_'):
    """
    Generate a slug in ASCII-only form
    :param text: Text to slugify
    :param delim: Delimiter to join
    :return: str slug
    """
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode(word).split())
    return delim.join(result)


def gcfg():
    _config = Config.query.one()
    if not _config:
        return {'app_name': "ree2bits"}
    return {'app_name': _config.app_name}


def gen_random_str(size=10):
    """
    Generate random string
    :param size: Size of string
    :return: Random string
    """
    return ''.join(random.choice(string.ascii_uppercase +
                                 string.ascii_lowercase +
                                 string.digits) for _ in range(size))


def path_or_none(fbase, ftype, fname):
    """
    Return path or none
    :param fbase: Base directory
    :param ftype: Type directory
    :param fname: Filename
    :return: Full path or None
    """
    if not fbase or not ftype or not fname:
        return None
    fpath = os.path.join(fbase, ftype, fname)
    return fpath if os.path.isfile(fpath) else None


def generate_uniques_apitoken():
    """
    Generate an unique API Token
    :return: Dict of token and secret pair
    """
    while 1:
        tmp_token = gen_random_str(20)
        tmp_secret = gen_random_str(20)

        blip = Apitoken.query.filter_by(token=tmp_token,
                                        secret=tmp_secret).first()
        if blip:
            continue
        else:
            return {"token": tmp_token, "secret": tmp_secret}

    return None


def f7(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def dt_utc_to_user_tz(dt, user=None):
    if not user:
        user = current_user
    user_tz = pytz.timezone(user.timezone)
    if dt.tzinfo == user_tz:
        return dt  # already converted
    utc_dt = pytz.timezone('UTC').localize(dt)  # Makes a naive-UTC DateTime
    return utc_dt.astimezone(user_tz)           # Then convert it to the user_tz


def show_date_no_offset(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


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
        rv['message'] = self.message
        rv['status'] = 'error'
        rv['code'] = self.status_code
        return rv


def is_admin():
    adm = Role.query.filter(Role.name == 'admin').first()
    if not current_user or not current_user.is_authenticated or not adm:
        return False
    if adm in current_user.roles:
        return True
    return False


def add_log(category, level, message):
    if not category or not level or not message:
        print("!! Fatal error in add_log() one of three variables not set")
    print("[LOG][{0}][{1}] {2}".format(level, category, message))
    a = Logging(category=category, level=level, message=message)
    db.session.add(a)
    db.session.commit()


def duration_human(seconds):
    seconds = int(round(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    years, days = divmod(days, 365.242199)

    minutes = int(minutes)
    hours = int(hours)
    days = int(days)
    years = int(years)

    if years > 0:
        return '%d year' % years + 's' * (years != 1)
    elif days > 0:
        return '%d day' % days + 's' * (days != 1)
    elif hours > 0:
        return '%d hour' % hours + 's' * (hours != 1)
    elif minutes > 0:
        return '%d minute' % minutes + 's' * (minutes != 1)
    else:
        return 'right now'
