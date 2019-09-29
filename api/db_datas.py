import click
from models import db, Sound, User
from utils.flake_id import gen_flakeid
from sqlalchemy.dialects.postgresql import UUID
from utils.defaults import Reel2bitsDefaults
import os
from flask.cli import with_appcontext
from flask import current_app


@click.group()
def db_datas():
    """
    Datas migrations sometimes needed.

    Run them only one time unless specified BREAKING.
    """
    pass


@db_datas.command(name="001-generate-tracks-uuids")
@with_appcontext
def generate_tracks_uuid():
    """
    Generate tracks UUIDs when missing (41_7eb56606e9d6)

    non breaking.
    """
    for sound in db.session.query(Sound).all():
        if not sound.flake_id:
            sound.flake_id = UUID(int=gen_flakeid())
    db.session.commit()


@db_datas.command(name="002-set-local-users")
@with_appcontext
def set_local_users():
    """
    Set User.local == user.actor.local (46_a3ada8658a05)

    non breaking.
    """
    for user in db.session.query(User).all():
        if len(user.actor) >= 1:
            if user.actor[0]:
                user.local = user.actor[0].is_local()
    db.session.commit()


@db_datas.command(name="003-set-user-quota")
@with_appcontext
def set_uset_quota():
    """
    Set default user quota (52_d37e30db3df1)

    non breaking.
    """
    for user in db.session.query(User).all():
        if not user.quota:
            user.quota = Reel2bitsDefaults.user_quotas_default
        if not user.quota_count:
            user.quota_count = 0
    db.session.commit()


@db_datas.command(name="004-update-file-sizes")
@with_appcontext
def update_file_sizes():
    """
    Update track files and transcode sizes (52_d37e30db3df1)

    non breaking.
    """
    for track in Sound.query.filter(Sound.file_size.is_(None)).all():
        track.file_size = os.path.getsize(
            os.path.join(current_app.config["UPLOADED_SOUNDS_DEST"], track.path_sound(orig=True))
        )
        if track.transcode_needed:
            track.transcode_file_size = os.path.getsize(
                os.path.join(current_app.config["UPLOADED_SOUNDS_DEST"], track.path_sound(orig=False))
            )
    db.session.commit()


@db_datas.command(name="005-update-user-quotas")
@with_appcontext
def update_user_quotas():
    """
    Update user quotas

    non breaking.
    """
    for user in User.query.filter(User.local.is_(True)).all():
        print(f"computing for {user.name} ({user.id})")
        user.quota_count = user.total_files_size()
    db.session.commit()
