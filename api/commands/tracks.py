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
def regenerate_waveform(slug, all):
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

        if sound.transcode_needed:
            fname = os.path.join(current_app.config["UPLOADED_SOUNDS_DEST"], sound.user.slug, sound.filename_transcoded)
        else:
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


@tracks.command(name="create-missing-activities")
@with_appcontext
def create_missing_activities():
    """
    Create all missing Actvities for all local tracks.
    """
    current_app.config["SERVER_NAME"] = current_app.config["REEL2BITS_HOSTNAME"]
    with current_app.app_context():
        sounds = Sound.query.filter(Sound.activity_id.is_(None)).all()
        if not sounds or len(sounds) == 0:
            print("No tracks are missing activities")
            exit

        for sound in sounds:
            print(f"Processing activity for {sound.id}, {sound.slug}")
            from tasks import federate_new_sound  # avoid import loop

            sound.activity_id = federate_new_sound(sound)
            db.session.commit()
