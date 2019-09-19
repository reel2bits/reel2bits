from __future__ import print_function

import contextlib
import os
import wave
import time

import mutagen
from pymediainfo import MediaInfo

from models import db, SoundInfo, Sound
from utils.various import (
    get_waveform,
    create_png_waveform,
    duration_human,
    add_user_log,
    generate_audio_dat_file,
    add_log,
)
from pydub import AudioSegment
from os.path import splitext
from flask import current_app


def get_basic_infos(fname):
    mi = MediaInfo.parse(fname)
    mig = mi.tracks[0]
    mt = mig.format

    accepted_types = ["Wave", "MPEG Audio", "FLAC", "Ogg"]
    if mt not in accepted_types:
        return mt

    print("- File is type {0}".format(mt))

    # We are going to get: duration (in seconds), format (bits), rate (Hz),
    # channels (count), codec (or not)
    infos = {
        "duration": None,
        "format": None,
        "rate": None,
        "channels": None,
        "codec": None,
        "bitrate": None,
        "bitrate_mode": None,
        "type": None,
        "type_human": None,
    }

    # WAV
    if mt == "Wave":
        with contextlib.closing(wave.open(fname, "r")) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)

            infos["duration"] = round(duration, 1)
            infos["channels"] = f.getnchannels()
            infos["rate"] = f.getframerate()
            infos["codec"] = "PCM"
            infos["format"] = f.getsampwidth() * 8
            infos["type"] = "WAV"
        infos["type_human"] = "WAV"
    # MP3
    elif mt == "MPEG Audio":
        muta = mutagen.File(fname)
        if muta is None:
            print("! ERROR mutagen is null")
            return infos
        infos["duration"] = muta.info.length
        infos["channels"] = muta.info.channels
        infos["rate"] = muta.info.sample_rate
        infos["codec"] = muta.info.encoder_info
        infos["bitrate"] = muta.info.bitrate
        if muta.info.bitrate_mode == mutagen.mp3.BitrateMode.CBR:
            infos["bitrate_mode"] = "CBR"
        elif muta.info.bitrate_mode == mutagen.mp3.BitrateMode.VBR:
            infos["bitrate_mode"] = "VBR"
        else:
            infos["bitrate_mode"] = "ABR"
        infos["type"] = "MP3"
        infos["type_human"] = "Mpeg 3"
    # OGG
    elif mt == "Ogg":
        muta = mutagen.File(fname)
        if muta is None:
            print("! ERROR mutagen is null")
            return infos
        infos["duration"] = muta.info.length
        infos["channels"] = muta.info.channels
        infos["rate"] = muta.info.sample_rate
        infos["bitrate"] = muta.info.bitrate
        infos["type"] = "OGG"
        infos["type_human"] = "Ogg Vorbis"
    # FLAC
    elif mt == "FLAC":
        muta = mutagen.File(fname)
        if muta is None:
            print("! ERROR mutagen is null")
            return infos
        infos["duration"] = muta.info.length
        infos["channels"] = muta.info.channels
        infos["rate"] = muta.info.sample_rate
        infos["bitrate"] = muta.info.bitrate
        if "encoder" in muta.vc:
            infos["codec"] = " ".join(muta.vc["encoder"])
        infos["type"] = "FLAC"
        infos["type_human"] = "FLAC"
    else:
        print("! ERROR not supported")

    return infos


def get_waveform_infos(fname):
    return get_waveform(fname)


def work_transcode(sound_id):
    sound = Sound.query.get(sound_id)
    if not sound:
        print("- Cant find sound ID {id} in database".format(id=sound_id))
        return
    if not sound.transcode_needed:
        print("- Sound ID {id} doesn't need transcoding".format(id=sound_id))
        sound.transcode_state = Sound.TRANSCODE_DONE
        db.session.commit()
        add_user_log(
            sound.id,
            sound.user.id,
            "sounds",
            "info",
            "Transcoding not needed for: {0} -- {1}".format(sound.id, sound.title),
        )
        return
    if not sound.transcode_state == Sound.TRANSCODE_WAITING:
        print("- Sound ID {id} transcoding != TRANSCODE_WAITING".format(id=sound_id))
        return

    print("File: {0}: {1}".format(sound.id, sound.title))
    add_user_log(
        sound.id, sound.user.id, "sounds", "info", "Transcoding started for: {0} -- {1}".format(sound.id, sound.title)
    )

    fname = os.path.join(current_app.config["UPLOADED_SOUNDS_DEST"], sound.user.slug, sound.filename)
    _file, _ext = splitext(fname)

    _start = time.time()

    a = AudioSegment.from_file(fname)
    a.export("{0}.mp3".format(_file), format="mp3", bitrate="196k")

    print("From: {0}".format(fname))
    print("Transcoded: {0}.mp3".format(_file))
    elapsed = time.time() - _start
    print("Transcoding done: ({0}) {1}".format(elapsed, duration_human(elapsed)))

    sound.transcode_state = Sound.TRANSCODE_DONE

    info = sound.sound_infos.first()
    info.done_waveform = False

    _a, _b = splitext(sound.filename)
    sound.filename_transcoded = "{0}.mp3".format(_a)
    db.session.commit()

    add_user_log(
        sound.id, sound.user.id, "sounds", "info", "Transcoding finished for: {0} -- {1}".format(sound.id, sound.title)
    )


def work_metadatas(sound_id, force=False):
    # force is unused for now
    sound = Sound.query.get(sound_id)
    if not sound:
        print("- Cant find sound ID %(id)s in database".format(id=sound_id))
        return

    add_user_log(
        sound.id,
        sound.user.id,
        "sounds",
        "info",
        "Metadatas gathering started for: {0} -- {1}".format(sound.id, sound.title),
    )

    _infos = sound.sound_infos.first()

    if not _infos:
        _infos = SoundInfo()
        _infos.sound_id = sound.id

    # Generate Basic infos

    fname = os.path.join(current_app.config["UPLOADED_SOUNDS_DEST"], sound.user.slug, sound.filename)
    basic_infos = None
    if not _infos.done_basic:
        basic_infos = get_basic_infos(fname)
        if type(basic_infos) != dict:
            # cannot process further
            print(f"- MIME: '{basic_infos}' is not supported")
            add_log("global", "ERROR", f"Unsupported audio format: {basic_infos}")
            return False

    if not _infos.done_basic or force:
        print("- WORKING BASIC on {0}, {1}".format(sound.id, sound.filename))
        print("- Our file got basic infos: {0}".format(basic_infos))
        _infos.duration = basic_infos["duration"]
        _infos.channels = basic_infos["channels"]
        _infos.rate = basic_infos["rate"]
        _infos.codec = basic_infos["codec"]
        _infos.format = basic_infos["format"]
        _infos.bitrate = basic_infos["bitrate"]
        _infos.bitrate_mode = basic_infos["bitrate_mode"]
        _infos.done_basic = True
        _infos.type = basic_infos["type"]
        _infos.type_human = basic_infos["type_human"]

    if not _infos.done_waveform or force:
        if sound.transcode_state == Sound.TRANSCODE_DONE:
            _f, _e = splitext(fname)
            fname_t = "{0}.mp3".format(_f)
            print("- WORKING ON TRANSCODED FOR WAVEFORM")
        else:
            fname_t = fname

        print("- GENERATING AUDIO DAT FILE")
        dat_file_name = generate_audio_dat_file(fname_t)

        print("- WORKING WAVEFORM on {0}, {1}".format(sound.id, sound.filename))
        waveform_infos = get_waveform_infos(dat_file_name)
        print("- Our file got waveform infos: {0}".format(waveform_infos))
        _infos.waveform = waveform_infos
        if not waveform_infos:
            _infos.waveform_error = True
            add_user_log(
                sound.id,
                sound.user.id,
                "sounds",
                "info",
                "Got an error when generating waveform" " for: {0} -- {1}".format(sound.id, sound.title),
            )
        else:
            fdir_wf = os.path.join(current_app.config["UPLOADS_DEFAULT_DEST"], "waveforms", sound.user.slug)
            fname_wf = os.path.join(fdir_wf, sound.filename)

            if not os.path.isdir(fdir_wf):
                os.makedirs(fdir_wf)

            create_png_waveform(dat_file_name, fname_wf)

        # Delete the temporary dat file
        os.unlink(dat_file_name)

        _infos.done_waveform = True

    db.session.add(_infos)
    db.session.commit()

    add_user_log(
        sound.id,
        sound.user.id,
        "sounds",
        "info",
        "Metadatas gathering finished for: {0} -- {1}".format(sound.id, sound.title),
    )
    return True
