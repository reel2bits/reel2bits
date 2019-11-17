import datetime
import os

from flask import current_app, url_for
from flask_security import SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_security.utils import verify_password
from flask_sqlalchemy import SQLAlchemy
from slugify import slugify
from sqlalchemy import event, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy.sql import func
from sqlalchemy_searchable import make_searchable
from sqlalchemy_utils.types.choice import ChoiceType
from sqlalchemy_utils.types.url import URLType
from little_boxes.key import Key as LittleBoxesKey
from activitypub.utils import ap_url
from activitypub.vars import DEFAULT_CTX
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import text as sa_text
from little_boxes import activitypub as ap
from urllib.parse import urlparse
from authlib.flask.oauth2.sqla import OAuth2ClientMixin, OAuth2AuthorizationCodeMixin, OAuth2TokenMixin
import time
import uuid
from utils.defaults import Reel2bitsDefaults


db = SQLAlchemy()
make_searchable(db.metadata)

# #### Base ####


class CaseInsensitiveComparator(Comparator):
    def __eq__(self, other):
        return func.lower(self.__clause_element__()) == func.lower(other)


class Config(db.Model):
    __tablename__ = "config"

    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(255), default=None)
    app_description = db.Column(db.Text)
    user_quota = db.Column(db.BigInteger, default=Reel2bitsDefaults.user_quotas_default)
    announcement = db.Column(db.Text, nullable=True)


# #### User ####

roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, info={"label": "Name"})
    description = db.Column(db.String(255), info={"label": "Description"})

    __mapper_args__ = {"order_by": name}


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_token"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=False), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    expires_at = db.Column(db.DateTime(timezone=False), nullable=True)
    used = db.Column(db.Boolean(), default=False)

    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=True, info={"label": "Email"})
    name = db.Column(db.String(255), nullable=False, info={"label": "Username"})
    password = db.Column(db.String(255), nullable=True, info={"label": "Password"})
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())

    created_at = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=False), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    display_name = db.Column(db.String(30), nullable=True, info={"label": "Display name"})

    locale = db.Column(db.String(5), default="en")

    timezone = db.Column(db.String(255), nullable=False, default="UTC")  # Managed and fed by pytz

    flake_id = db.Column(UUID(as_uuid=True), unique=False, nullable=True)

    # should be removed since User.name is URL friendly
    slug = db.Column(db.String(255), nullable=True)

    # User default quota, database default is the one from the hardcoded value
    # It is overriden when registering with the app config one, here it is only
    # if there is no quota defined, and in cas of, to avoid issues.
    # Both are in bytes
    quota = db.Column(db.BigInteger(), default=Reel2bitsDefaults.user_quotas_default)
    # This should be updated on each upload and deletes
    quota_count = db.Column(db.BigInteger(), default=0)

    avatar_filename = db.Column(db.String(255), unique=False, nullable=True)

    local = db.Column(db.Boolean(), default=True)

    # Relations

    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic"), cascade_backrefs=False
    )
    password_reset_tokens = db.relationship("PasswordResetToken", backref="user", lazy="dynamic", cascade="delete")
    user_loggings = db.relationship("UserLogging", backref="user", lazy="dynamic", cascade="delete")
    loggings = db.relationship("Logging", backref="user", lazy="dynamic", cascade="delete")

    sounds = db.relationship("Sound", backref="user", lazy="dynamic", cascade="delete")
    albums = db.relationship("Album", backref="user", lazy="dynamic", cascade="delete")

    __mapper_args__ = {"order_by": name}

    def is_admin(self):
        admin_role = db.session.query(Role).filter(Role.name == "admin").one()
        return admin_role in self.roles

    def join_roles(self, string):
        return string.join([i.description for i in self.roles])

    @staticmethod
    def generate_slug(target, value, oldvalue, initiator):
        if value and (not target.slug or value != oldvalue):
            target.slug = value

    @hybrid_property
    def name_insensitive(self):
        return self.name.lower()

    @name_insensitive.comparator
    def name_insensitive(cls):
        return CaseInsensitiveComparator(cls.name)

    def __repr__(self):
        return f"<User(id='{self.id}', name='{self.name}')>"

    def username(self):
        if not self.display_name:
            return self.name
        elif len(self.display_name) > 0:
            return self.display_name
        else:
            return self.name

    def get_user_id(self):
        return self.id

    def check_password(self, password):
        return verify_password(password, self.password)

    def total_files_size(self):
        c = (
            db.session.query(func.sum(Sound.file_size), func.sum(Sound.transcode_file_size))
            .filter(Sound.user_id == self.id)
            .one()
        )
        return (c[0] or 0) + (c[1] or 0)

    def path_avatar(self):
        if self.avatar_filename:
            return os.path.join(self.slug, self.avatar_filename)
        else:
            return None

    def acct(self):
        if self.local:
            return self.name
        else:
            name = self.name
            if not len(self.actor) > 0:
                print(f"user {self.id} has no actor")
                return self.name  # *shrug*
            instance = self.actor[0].domain
            return f"{name}@{instance}"

    # Delete files file when COMMIT DELETE
    def __commit_delete__(self):
        print("COMMIT DELETE: Deleting files")
        if self.avatar_filename:
            fname = os.path.join(current_app.config["UPLOADED_AVATARS_DEST"], self.avatar_filename())
            if os.path.isfile(fname):
                os.unlink(fname)
            else:
                print(f"!!! COMMIT DELETE USER cannot delete avatar file {fname}")


event.listen(User.name, "set", User.generate_slug, retval=False)


user_datastore = SQLAlchemyUserDatastore(db, User, Role)


class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = "oauth2_client"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User")


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = "oauth2_code"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User")


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = "oauth2_token"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User")

    def is_refresh_token_expired(self):
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at < time.time()


# #### Logging ####


class Logging(db.Model):
    __tablename__ = "logging"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255), nullable=False, default="General")
    level = db.Column(db.String(255), nullable=False, default="INFO")
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=False), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable=True)

    __mapper_args__ = {"order_by": timestamp.desc()}


class UserLogging(db.Model):
    __tablename__ = "user_logging"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255), nullable=False, default="General")
    level = db.Column(db.String(255), nullable=False, default="INFO")
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=False), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    item_id = db.Column(db.Integer(), nullable=True)

    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable=False)

    __mapper_args__ = {"order_by": timestamp.desc()}


# #### Tracks ####


class SoundInfo(db.Model):
    __tablename__ = "sound_info"

    id = db.Column(db.Integer, primary_key=True)
    duration = db.Column(db.Float, nullable=True)
    format = db.Column(db.String(255), nullable=True)
    rate = db.Column(db.String(255), nullable=True)
    channels = db.Column(db.Integer, nullable=True)
    codec = db.Column(db.String(255), nullable=True)
    waveform = db.Column(db.Text, nullable=True)
    waveform_error = db.Column(db.Boolean, default=False)
    bitrate = db.Column(db.Integer, nullable=True)
    bitrate_mode = db.Column(db.String(10), nullable=True)
    type = db.Column(db.String(20), nullable=True)
    type_human = db.Column(db.String(20), nullable=True)

    # States markers
    done_basic = db.Column(db.Boolean, default=False)
    done_waveform = db.Column(db.Boolean, default=False)

    sound_id = db.Column(db.Integer(), db.ForeignKey("sound.id"), nullable=False)


# Table for association between Sound and SoundTag
sound_tags = db.Table(
    "sound_tags",
    db.Column("tag_id", db.Integer, db.ForeignKey("sound_tag.id"), primary_key=True),
    db.Column("sound_id", db.Integer, db.ForeignKey("sound.id"), primary_key=True),
    PrimaryKeyConstraint("tag_id", "sound_id"),
)
# Same but for albums
album_tags = db.Table(
    "album_tags",
    db.Column("tag_id", db.Integer, db.ForeignKey("sound_tag.id"), primary_key=True),
    db.Column("album_id", db.Integer, db.ForeignKey("album.id"), primary_key=True),
    PrimaryKeyConstraint("tag_id", "album_id"),
)


class SoundTag(db.Model):
    __tablename__ = "sound_tag"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)


class Sound(db.Model):
    __tablename__ = "sound"
    TRANSCODE_WAITING = 0
    TRANSCODE_PROCESSING = 1
    TRANSCODE_DONE = 2
    TRANSCODE_ERROR = 3

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    uploaded = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    updated = db.Column(
        db.DateTime(timezone=False), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    genre = db.Column(db.String(255), nullable=True)
    tags = db.relationship("SoundTag", secondary=sound_tags, lazy="subquery", backref=db.backref("sounds", lazy=True))
    licence = db.Column(db.Integer, nullable=False, server_default="0")
    description = db.Column(db.UnicodeText(), nullable=True)
    private = db.Column(db.Boolean(), default=False, nullable=True)
    slug = db.Column(db.String(255), unique=True, nullable=True)
    remote_uri = db.Column(db.String(255), unique=False, nullable=True)
    filename = db.Column(db.String(255), unique=False, nullable=True)
    filename_transcoded = db.Column(db.String(255), unique=False, nullable=True)

    filename_orig = db.Column(db.String(255), unique=False, nullable=True)
    album_order = db.Column(db.Integer, nullable=True)

    artwork_filename = db.Column(db.String(255), unique=False, nullable=True)
    remote_artwork_uri = db.Column(db.String(255), unique=False, nullable=True)

    transcode_needed = db.Column(db.Boolean(), default=False, nullable=True)
    transcode_state = db.Column(db.Integer(), default=0, nullable=False)
    # 0 nothing / default / waiting, 1 processing, 2 done, 3 error

    # both are bytes
    file_size = db.Column(db.BigInteger)
    transcode_file_size = db.Column(db.BigInteger)

    flake_id = db.Column(UUID(as_uuid=True), unique=False, nullable=True)

    # relations
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable=False)
    album_id = db.Column(db.Integer(), db.ForeignKey("album.id"), nullable=True)
    activity_id = db.Column(db.Integer(), db.ForeignKey("activity.id"), nullable=True)

    sound_infos = db.relationship("SoundInfo", backref="sound_info", lazy="dynamic", cascade="delete")
    activity = db.relationship("Activity")

    __mapper_args__ = {"order_by": uploaded.desc()}

    def elapsed(self):
        el = datetime.datetime.utcnow() - self.uploaded
        return el.total_seconds()

    def path_sound(self, orig=False):
        username = self.user.slug
        if self.remote_uri:
            username = f"remote_{self.user.slug}"
        if self.transcode_needed and self.transcode_state == self.TRANSCODE_DONE and not orig:
            return os.path.join(username, self.filename_transcoded)
        else:
            return os.path.join(username, self.filename)

    def path_artwork(self):
        if self.artwork_filename:
            return os.path.join(self.user.slug, self.artwork_filename)
        else:
            return None

    def licence_info(self):
        return Reel2bitsDefaults.known_licences[self.licence]

    def get_title(self):
        if not self.title:
            return self.filename
        return self.title

    def processing_done(self):
        return self.transcode_state == self.TRANSCODE_DONE

    def is_ready(self):
        infos = self.sound_infos.first()
        if not infos:
            return False
        return self.processing_done() and infos.done_basic

    # Delete files file when COMMIT DELETE
    def __commit_delete__(self):
        print("COMMIT DELETE: Deleting files")
        fname = os.path.join(current_app.config["UPLOADED_SOUNDS_DEST"], self.path_sound(orig=True))
        if os.path.isfile(fname):
            os.unlink(fname)
        else:
            print(f"!!! COMMIT DELETE SOUND cannot delete orig file {fname}")

        if self.transcode_needed:
            fname = os.path.join(current_app.config["UPLOADED_SOUNDS_DEST"], self.path_sound(orig=False))
            if os.path.isfile(fname):
                os.unlink(fname)
            else:
                print(f"!!! COMMIT DELETE SOUND cannot delete transcoded file {fname}")

        if self.artwork_filename:
            fname = os.path.join(current_app.config["UPLOADED_ARTWORKSOUNDS_DEST"], self.path_artwork())
            if os.path.isfile(fname):
                os.unlink(fname)
            else:
                print(f"!!! COMMIT DELETE SOUND cannot delete artwork file {fname}")


class Album(db.Model):
    __tablename__ = "album"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    created = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    updated = db.Column(
        db.DateTime(timezone=False), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    genre = db.Column(db.String(255), nullable=True)
    tags = db.relationship("SoundTag", secondary=album_tags, lazy="subquery", backref=db.backref("albums", lazy=True))
    description = db.Column(db.UnicodeText(), nullable=True)
    private = db.Column(db.Boolean(), default=False, nullable=True)
    slug = db.Column(db.String(255), unique=True, nullable=True)

    artwork_filename = db.Column(db.String(255), unique=False, nullable=True)

    flake_id = db.Column(UUID(as_uuid=True), unique=False, nullable=True)

    # relations
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable=False)
    sounds = db.relationship("Sound", backref="album", lazy="dynamic")

    __mapper_args__ = {"order_by": created.desc()}

    def elapsed(self):
        el = datetime.datetime.utcnow() - self.created
        return el.total_seconds()

    def path_artwork(self):
        if self.artwork_filename:
            return os.path.join(self.user.slug, self.artwork_filename)
        else:
            return None

    # Delete files file when COMMIT DELETE
    def __commit_delete__(self):
        if self.artwork_filename:
            fname = os.path.join(current_app.config["UPLOADED_ARTWORKALBUMS_DEST"], self.path_artwork())
            if os.path.isfile(fname):
                os.unlink(fname)
            else:
                print(f"!!! COMMIT DELETE ALBUM cannot delete artwork file {fname}")


@event.listens_for(Sound, "after_update")
@event.listens_for(Sound, "after_insert")
def make_sound_slug(mapper, connection, target):
    if not target.title or target.title == "":
        title = "{0} {1}".format(target.id, target.filename_orig)
    else:
        if slugify(target.title) == "":
            title = "{0} {1}".format(target.id, target.filename_orig)
        else:
            title = "{0} {1}".format(target.id, target.title)

    slug = slugify(title[:255])
    connection.execute(Sound.__table__.update().where(Sound.__table__.c.id == target.id).values(slug=slug))


@event.listens_for(Sound, "after_insert")
def generate_sound_flakeid(mapper, connection, target):
    if not target.flake_id:
        flake_id = uuid.UUID(int=current_app.flake_id.get())
        connection.execute(Sound.__table__.update().where(Sound.__table__.c.id == target.id).values(flake_id=flake_id))


@event.listens_for(Sound, "after_delete")
@event.listens_for(Album, "after_delete")
def delete_files(mapper, connection, target):
    target.__commit_delete__()


@event.listens_for(Album, "after_update")
@event.listens_for(Album, "after_insert")
def make_album_slug(mapper, connection, target):
    title = "{0} {1}".format(target.id, target.title)
    slug = slugify(title[:255])
    connection.execute(Album.__table__.update().where(Album.__table__.c.id == target.id).values(slug=slug))


@event.listens_for(Album, "after_insert")
def generate_album_flakeid(mapper, connection, target):
    if not target.flake_id:
        flake_id = uuid.UUID(int=current_app.flake_id.get())
        connection.execute(Album.__table__.update().where(Album.__table__.c.id == target.id).values(flake_id=flake_id))


@event.listens_for(User, "after_update")
def update_user_actor(mapper, connection, target):
    connection.execute(
        Actor.__table__.update().where(Actor.__table__.c.user_id == target.id).values(name=target.display_name)
    )


# #### Federation ####

ACTOR_TYPE_CHOICES = [
    ("Person", "Person"),
    ("Application", "Application"),
    ("Group", "Group"),
    ("Organization", "Organization"),
    ("Service", "Service"),
]


# This table keeps followings in every way
# (remote to local, local to local, to remote...)
# Query this table directly to get list for a specific actor or target
class Follower(db.Model):
    __tablename__ = "followers"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), server_default=sa_text("uuid_generate_v4()"), unique=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("actor.id"))
    target_id = db.Column(db.Integer, db.ForeignKey("actor.id"))
    activity_url = db.Column(URLType(), unique=True, nullable=True)
    creation_date = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    modification_date = db.Column(db.DateTime(timezone=False), onupdate=datetime.datetime.now)

    actor = db.relationship("Actor", foreign_keys=[actor_id])
    target = db.relationship("Actor", foreign_keys=[target_id])

    __table_args__ = (UniqueConstraint("actor_id", "target_id", name="unique_following"),)

    def __repr__(self):
        return f"<Follower(id='{self.id}', actor_id='{self.actor_id}', target_id='{self.target_id}')>"

    def follow_back(self):
        f = (
            db.session.query(Follower.id)
            .filter(Follower.actor_id == self.target_id, Follower.target_id == self.actor_id)
            .first()
        )
        return f


class Actor(db.Model):
    __tablename__ = "actor"
    ap_type = "Actor"

    id = db.Column(db.Integer, primary_key=True)

    url = db.Column(URLType(), unique=True, index=True)
    outbox_url = db.Column(URLType())
    inbox_url = db.Column(URLType())
    following_url = db.Column(URLType(), nullable=True)
    followers_url = db.Column(URLType(), nullable=True)
    shared_inbox_url = db.Column(URLType(), nullable=True)
    type = db.Column(ChoiceType(ACTOR_TYPE_CHOICES), server_default="Person")
    name = db.Column(db.String(200), nullable=True)
    domain = db.Column(db.String(1000), nullable=False)
    summary = db.Column(db.String(500), nullable=True)
    preferred_username = db.Column(db.String(200), nullable=True)
    public_key = db.Column(db.String(5000), nullable=True)
    private_key = db.Column(db.String(5000), nullable=True)
    creation_date = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    last_fetch_date = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    manually_approves_followers = db.Column(db.Boolean, nullable=True, server_default=None)
    # Who follows self
    followers = db.relationship("Follower", backref="followers", primaryjoin=id == Follower.target_id, lazy="dynamic")
    # Who self follows
    followings = db.relationship("Follower", backref="followings", primaryjoin=id == Follower.actor_id, lazy="dynamic")
    # Relation on itself, intermediary with actor and target
    # By using an Association Object, which isn't possible except by using
    # two relations. This may be better than only one, and some hackish things
    # by querying directly the old db.Table definition

    meta_deleted = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    user = db.relationship("User", backref=db.backref("actor"))

    __table_args__ = (UniqueConstraint("domain", "preferred_username", name="_domain_pref_username_uc"),)

    def __repr__(self):
        return f"<Actor(id='{self.id}', user_id='{self.user_id}', preferredUsername='{self.preferred_username}', domain='{self.domain}')>"

    def webfinger_subject(self):
        return f"{self.preferred_username}@{self.domain}"

    def private_key_id(self):
        return f"{self.url}#main-key"

    def mention_username(self):
        return f"@{self.preferred_username}@{self.domain}"

    def is_local(self):
        return self.domain == current_app.config["AP_DOMAIN"]

    def follow(self, activity_url, target):
        current_app.logger.debug(f"saving: {self.id} following {target.id}")

        rel = Follower.query.filter(Follower.actor_id == self.id, Follower.target_id == target.id).first()

        if not rel:
            rel = Follower()
            rel.actor_id = self.id
            rel.target_id = target.id
            rel.activity_url = activity_url
            db.session.add(rel)
            db.session.commit()

    def unfollow(self, target):
        current_app.logger.debug(f"saving: {self.id} unfollowing {target.id}")

        rel = Follower.query.filter(Follower.actor_id == self.id, Follower.target_id == target.id).first()
        if rel:
            db.session.delete(rel)
            db.session.commit()

    def is_followed_by(self, target):
        print(f"is {self.preferred_username} followed by {target.preferred_username} ?")
        return self.followers.filter(Follower.actor_id == target.id).first()

    def is_following(self, target):
        print(f"is {self.preferred_username} following {target.preferred_username} ?")
        return self.followings.filter(Follower.target_id == target.id).first()

    def to_dict(self):
        if self.user.path_avatar():
            url_avatar = url_for("get_uploads_stuff", thing="avatars", stuff=self.user.path_avatar(), _external=True)
        else:
            url_avatar = f"{current_app.config['REEL2BITS_URL']}/static/userpic_placeholder.svg"

        return {
            "@context": DEFAULT_CTX,
            "id": self.url,
            "type": self.type.code,
            "preferredUsername": self.preferred_username,
            "name": self.name,
            "inbox": self.inbox_url,
            "outbox": self.outbox_url,
            "followers": self.followers_url,
            "following": self.following_url,
            "manuallyApprovesFollowers": self.manually_approves_followers,
            "publicKey": {"id": self.private_key_id(), "owner": self.url, "publicKeyPem": self.public_key},
            "endpoints": {"sharedInbox": self.shared_inbox_url},
            "icon": {"type": "Image", "url": url_avatar},
        }


class Activity(db.Model):
    __tablename__ = "activity"
    id = db.Column(db.Integer, primary_key=True)

    actor_id = db.Column(db.Integer, db.ForeignKey("actor.id"), nullable=True)
    actor = db.relationship("Actor", backref=db.backref("actor"))

    uuid = db.Column(UUID(as_uuid=True), server_default=sa_text("uuid_generate_v4()"), unique=True)
    url = db.Column(URLType(), unique=True, nullable=True)
    type = db.Column(db.String(100), index=True)
    box = db.Column(db.String(100))
    payload = db.Column(JSONB())
    creation_date = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    delivered = db.Column(db.Boolean, default=None, nullable=True)
    delivered_date = db.Column(db.DateTime(timezone=False), nullable=True)
    local = db.Column(db.Boolean, default=True)
    meta_deleted = db.Column(db.Boolean, default=False)
    meta_undo = db.Column(db.Boolean, default=False)
    meta_pinned = db.Column(db.Boolean, default=False)


def create_actor(user):
    """
    :param user: an User object
    :return: an Actor object
    """
    actor = Actor()

    # Init a new Keypair for this user
    key = LittleBoxesKey(owner=user.name)
    key.new()

    actor.preferred_username = user.name
    actor.domain = current_app.config["AP_DOMAIN"]
    actor.type = "Person"
    actor.name = user.display_name
    actor.manually_approves_followers = False
    actor.url = ap_url("url", user.name)
    actor.shared_inbox_url = ap_url("shared_inbox", user.name)
    actor.inbox_url = ap_url("inbox", user.name)
    actor.outbox_url = ap_url("outbox", user.name)
    actor.private_key = key.privkey_pem
    actor.public_key = key.pubkey_pem
    actor.followers_url = ap_url("followers", user.name)
    actor.following_url = ap_url("followings", user.name)

    return actor


def create_remote_actor(activity_actor: ap.BaseActivity):
    """
    :param activity_actor: a Little Boxes Actor object
    :return: an Actor object
    """
    actor = Actor()
    actor.preferred_username = activity_actor.preferredUsername
    domain = urlparse(activity_actor.url)
    actor.domain = domain.netloc
    actor.type = "Person"
    actor.name = activity_actor.name
    actor.manually_approves_followers = False
    actor.url = activity_actor.id  # FIXME: or .id ??? [cf backend.py:52-53]
    actor.shared_inbox_url = activity_actor._data.get("endpoints", {}).get("sharedInbox")
    actor.inbox_url = activity_actor.inbox
    actor.outbox_url = activity_actor.outbox
    actor.public_key = activity_actor.get_key().pubkey_pem
    actor.summary = activity_actor.summary
    actor.followers_url = activity_actor.followers
    actor.following_url = activity_actor.following

    user = User()
    user.email = None
    user.name = activity_actor.preferredUsername
    user.password = None
    user.active = False
    user.confirmed_at = None
    user.display_name = activity_actor.name
    user.local = False

    actor.user = user

    # TODO: Avatar

    return actor, user


def update_remote_actor(actor_id: int, activity_actor: ap.BaseActivity) -> None:
    """
    :param actor_id: an Actor db ID
    :param activity_actor: a Little Boxes Actor object
    :return: nothing
    """
    actor = Actor.query.filter(Actor.id == actor_id).first()
    current_app.logger.debug(f"asked to update Actor {actor_id}: {activity_actor!r}")

    actor.preferred_username = activity_actor.preferredUsername
    domain = urlparse(activity_actor.url)
    actor.domain = domain.netloc
    actor.name = activity_actor.name
    actor.manually_approves_followers = False
    actor.url = activity_actor.id  # FIXME: or .id ??? [cf backend.py:52-53]
    actor.shared_inbox_url = activity_actor._data.get("endpoints", {}).get("sharedInbox")
    actor.inbox_url = activity_actor.inbox
    actor.outbox_url = activity_actor.outbox
    actor.public_key = activity_actor.get_key().pubkey_pem
    actor.summary = activity_actor.summary
    actor.followers_url = activity_actor.followers
    actor.following_url = activity_actor.following

    db.session.commit()


def strip_end(text, suffix):
    if not text.endswith(suffix):
        return text
    return text[: len(text) - len(suffix)]


def update_remote_track(actor_id: int, update: ap.Update) -> None:
    """
    :param actor_id: an Actor db ID
    :param obj: a Little Boxes Audio object
    :return: nothing
    """
    obj = update.get_object()
    current_app.logger.debug(f"asked to update a track {obj!r}")
    current_app.logger.debug(f"obj id {obj.id}")
    act_id = strip_end(obj.id, "/activity")
    original_activity = Activity.query.filter(Activity.url == act_id).first()
    if not original_activity:
        # TODO(dashie) we should fetch it if not found
        current_app.logger.error("fetching unknown activity not yet implemented")
        raise NotImplementedError

    update_activity = Activity.query.filter(Activity.url == strip_end(update.id, "/activity")).first()
    if not update_activity:
        current_app.logger.error(f"cannot get update activity from db {update!r}")
        return

    track = Sound.query.filter(Sound.activity_id == original_activity.id).first()
    if not track:
        current_app.logger.error(f"update_remote_track: {original_activity!r} has no associated sound")
        return

    # Update what is allowed to change
    # If not found they should fallback to the actual .thing of the object in db
    track.title = update_activity.payload.get("object", {}).get("name", track.title)
    track.description = update_activity.payload.get("object", {}).get("content", track.description)

    db.session.commit()
