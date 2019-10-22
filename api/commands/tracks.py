import click
from models import db, Sound
from flask.cli import with_appcontext
from flask import current_app
from os.path import splitext
from utils.various import get_waveform, generate_audio_dat_file
import os


@click.group()
def tracks():
    """
    Tracks commands.
    """
    pass


@tracks.command(name="regenerate-waveform")
@click.option("--slug", help="Specify slug to regenerate waveform")
@click.option("--all", default=False, is_flag=True, help="Process all tracks")
@with_appcontext
def list(slug, all):
    """
    Regenerate all waveforms or a single track.
    """
    sounds = []
    if slug:
        sound = Sound.query.filter(Sound.slug == slug).first()
        if sound:
            sounds.append(sound)
        else:
            print(f"No track matches the slug '{slug}'.")
            return
    elif all:
        sounds = Sound.query.all()
    else:
        print("No --slug= or --all, doing nothing, please --help")
        exit

    for sound in sounds:
        print(f"Processing waveform for {sound.id}, {sound.slug}")

        fname = os.path.join(current_app.config["UPLOADED_SOUNDS_DEST"], sound.user.slug, sound.filename)

        sound_infos = sound.sound_infos.first()
        if not sound_infos or not sound_infos.done_basic:
            print(" track is not processed, skip")
            continue

        if sound.transcode_state == Sound.TRANSCODE_DONE:
            _f, _e = splitext(fname)
            fname_t = "{0}.mp3".format(_f)
        else:
            fname_t = fname

        dat_file_name = generate_audio_dat_file(fname_t, sound_infos.duration)

        sound_infos.waveform = get_waveform(dat_file_name, sound_infos.duration)

        # Delete the temporary dat file
        os.unlink(dat_file_name)

    db.session.commit()
