from __future__ import print_function

import gzip
import os
import shutil
import urllib.parse
import urllib.error
import urllib.request
import xml.etree.ElementTree as ElementTree
import re
import datetime

from dateutil import parser
from flask import current_app

import magic
import mutagen
import wave
import contextlib
from models import db, User, Sound, SoundInfo
from utils import get_waveform, create_png_waveform


def get_basic_infos(fname):
    mt = magic.from_file(fname, mime=True)

    print("- File is type {0}".format(mt))

    # We are going to get: duration (in seconds), format (bits), rate (Hz), channels (count), codec (or not)
    infos = {'duration': None, 'format': None, 'rate': None, 'channels': None, 'codec': None,
             'bitrate': None, 'bitrate_mode': None, 'type': None, 'type_human': None}

    # WAV
    if mt == "audio/x-wav":
        with contextlib.closing(wave.open(fname, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)

            infos['duration'] = round(duration, 1)
            infos['channels'] = f.getnchannels()
            infos['rate'] = f.getframerate()
            infos['codec'] = "PCM"
            infos['format'] = f.getsampwidth() * 8
            infos['type'] = "WAV"
        infos['type_human'] = "WAV"
    # MP3
    elif mt == "audio/mpeg":
        muta = mutagen.File(fname)
        if muta is None:
            print("! ERROR mutagen is null")
            return infos
        infos['duration'] = muta.info.length
        infos['channels'] = muta.info.channels
        infos['rate'] = muta.info.sample_rate
        infos['codec'] = muta.info.encoder_info
        infos['bitrate'] = muta.info.bitrate
        if muta.info.bitrate_mode == mutagen.mp3.BitrateMode.CBR:
            infos['bitrate_mode'] = "CBR"
        elif muta.info.bitrate_mode == mutagen.mp3.BitrateMode.VBR:
            infos['bitrate_mode'] = "VBR"
        else:
            infos['bitrate_mode'] = "ABR"
        infos['type'] = "MP3"
        infos['type_human'] = "Mpeg 3"
    # OGG
    elif mt == "audio/ogg":
        muta = mutagen.File(fname)
        if muta is None:
            print("! ERROR mutagen is null")
            return infos
        infos['duration'] = muta.info.length
        infos['channels'] = muta.info.channels
        infos['rate'] = muta.info.sample_rate
        infos['bitrate'] = muta.info.bitrate
        infos['type'] = "OGG"
        infos['type_human'] = "Ogg Vorbis"
    # FLAC
    elif mt == "audio/x-flac" or mt == "audio/flac":
        muta = mutagen.File(fname)
        if muta is None:
            print("! ERROR mutagen is null")
            return infos
        infos['duration'] = muta.info.length
        infos['channels'] = muta.info.channels
        infos['rate'] = muta.info.sample_rate
        infos['bitrate'] = muta.info.bitrate
        if 'encoder' in muta.vc:
            infos['codec'] = ' '.join(muta.vc['encoder'])
        infos['type'] = "FLAC"
        infos['type_human'] = "FLAC"
    else:
        print("! ERROR not supported")

    return infos


def get_waveform_infos(fname):
    create_png_waveform(fname)
    return get_waveform(fname)


def cron_generate_sound_infos(dry_run=False, force=False):
    users = User.query.all()
    for user in users:
        print("- User {0}".format(user.name))
        for sound in user.sounds:
            _infos = sound.sound_infos.first()
            is_new = False

            if not _infos:
                _infos = SoundInfo()
                _infos.sound_id = sound.id
                is_new = True

            # Generate Basic infos

            fname = os.path.join(current_app.config['UPLOADED_SOUND_DEST'], sound.filename)

            if not _infos.done_basic or force:
                print("- WORKING BASIC on {0}, {1}".format(sound.id, sound.filename))
                basic_infos = get_basic_infos(fname)
                print("- Our file got basic infos: {0}".format(basic_infos))
                _infos.duration = basic_infos['duration']
                _infos.channels = basic_infos['channels']
                _infos.rate = basic_infos['rate']
                _infos.codec = basic_infos['codec']
                _infos.format = basic_infos['format']
                _infos.bitrate = basic_infos['bitrate']
                _infos.bitrate_mode = basic_infos['bitrate_mode']
                _infos.done_basic = True
                _infos.type = basic_infos['type']
                _infos.type_human = basic_infos['type_human']

            if not _infos.done_waveform or force:
                print("- WORKING WAVEFORM on {0}, {1}".format(sound.id, sound.filename))
                waveform_infos = get_waveform_infos(fname)
                print("- Our file got waveform infos: {0}".format(waveform_infos))
                _infos.waveform = waveform_infos
                _infos.done_waveform = True

            if not dry_run and is_new:
                db.session.add(_infos)

        print("- COMMIT for user {0}".format(user.name))
        if not dry_run:
            db.session.commit()
