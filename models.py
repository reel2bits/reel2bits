import datetime
import os

from flask_security import SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy
from slugify import slugify
from sqlalchemy import event
from sqlalchemy.sql import func
from sqlalchemy_searchable import make_searchable

db = SQLAlchemy()
make_searchable(db.metadata)

roles_users = db.Table('roles_users',
                       db.Column('user_id',
                                 db.Integer(),
                                 db.ForeignKey('user.id')),
                       db.Column('role_id',
                                 db.Integer(),
                                 db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False,
                     info={'label': 'Name'})
    description = db.Column(db.String(255), info={'label': 'Description'})

    __mapper_args__ = {"order_by": name}


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False,
                      info={'label': 'Email'})
    name = db.Column(db.String(255), unique=True, nullable=False,
                     info={'label': 'Name'})
    password = db.Column(db.String(255), nullable=False,
                         info={'label': 'Password'})
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())

    firstname = db.Column(db.String(32))
    lastname = db.Column(db.String(32))

    locale = db.Column(db.String(5), default="en")

    timezone = db.Column(db.String(255), nullable=False,
                         default='UTC')  # Managed and fed by pytz

    slug = db.Column(db.String(255), unique=True, nullable=True)

    roles = db.relationship('Role',
                            secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    apitokens = db.relationship('Apitoken',
                                backref='user',
                                lazy='dynamic',
                                cascade="delete")

    user_loggings = db.relationship('UserLogging', backref='user',
                                    lazy='dynamic', cascade="delete")
    loggings = db.relationship('Logging', backref='user',
                               lazy='dynamic', cascade="delete")

    sounds = db.relationship('Sound', backref='user',
                             lazy='dynamic', cascade="delete")
    albums = db.relationship('Album', backref='user',
                             lazy='dynamic', cascade="delete")

    __mapper_args__ = {"order_by": name}

    def join_roles(self, string):
        return string.join([i.description for i in self.roles])


class Apitoken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'),
                        nullable=False)
    token = db.Column(db.String(255), unique=True,
                      nullable=False, info={'label': 'Token'})
    secret = db.Column(db.String(255), unique=True,
                       nullable=False, info={'label': 'Secret'})


user_datastore = SQLAlchemyUserDatastore(db, User, Role)


class Config(db.Model):
    __tablename__ = "config"

    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(255), default=None)
    app_description = db.Column(db.Text)


class Logging(db.Model):
    __tablename__ = "logging"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255), nullable=False,
                         default="General")
    level = db.Column(db.String(255), nullable=False, default="INFO")
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=False),
                          server_default=func.now(), onupdate=func.now())

    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=True)

    __mapper_args__ = {"order_by": timestamp.desc()}


class UserLogging(db.Model):
    __tablename__ = "user_logging"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255), nullable=False, default="General")
    level = db.Column(db.String(255), nullable=False, default="INFO")
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=False),
                          server_default=func.now(), onupdate=func.now())

    sound_id = db.Column(db.Integer(), db.ForeignKey('sound.id'),
                         nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'),
                        nullable=False)

    __mapper_args__ = {"order_by": timestamp.desc()}


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

    sound_id = db.Column(db.Integer(), db.ForeignKey('sound.id'),
                         nullable=False)


class Sound(db.Model):
    __tablename__ = "sound"
    TRANSCODE_WAITING = 0
    TRANSCODE_PROCESSING = 1
    TRANSCODE_DONE = 2
    TRANSCODE_ERROR = 3

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    uploaded = db.Column(db.DateTime(timezone=False),
                         default=datetime.datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=False),
                        default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    # TODO genre
    # TODO tags
    # TODO picture ?
    licence = db.Column(db.Integer, nullable=False, server_default='0')
    description = db.Column(db.UnicodeText(), nullable=True)
    private = db.Column(db.Boolean(), default=False, nullable=True)
    slug = db.Column(db.String(255), unique=True, nullable=True)
    filename = db.Column(db.String(255), unique=False, nullable=True)
    filename_transcoded = db.Column(db.String(255), unique=False,
                                    nullable=True)

    filename_orig = db.Column(db.String(255), unique=False, nullable=True)
    album_order = db.Column(db.Integer, nullable=True)

    transcode_needed = db.Column(db.Boolean(), default=False, nullable=True)
    transcode_state = db.Column(db.Integer(), default=0, nullable=False)
    # 0 nothing / default / waiting, 1 processing, 2 done, 3 error

    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'),
                        nullable=False)
    album_id = db.Column(db.Integer(), db.ForeignKey('album.id'),
                         nullable=True)
    sound_infos = db.relationship('SoundInfo', backref='sound_info',
                                  lazy='dynamic', cascade="delete")
    user_loggings = db.relationship('UserLogging', backref='sound',
                                    lazy='dynamic', cascade="delete")

    timeline = db.relationship("Timeline", uselist=False,
                               back_populates="sound")

    __mapper_args__ = {"order_by": uploaded.desc()}

    def elapsed(self):
        print("db: {0}, now: {1}".format(self.uploaded,
                                         datetime.datetime.utcnow()))
        el = datetime.datetime.utcnow() - self.uploaded
        return el.total_seconds()

    def path_waveform(self):
        return os.path.join(self.user.slug, "{0}.png".format(self.filename))

    def path_sound(self, orig=False):
        if self.transcode_state == self.TRANSCODE_DONE and not orig:
            return os.path.join(self.user.slug, self.filename_transcoded)
        else:
            return os.path.join(self.user.slug, self.filename)

    def licence_info(self):
        return licences[self.licence]


class Album(db.Model):
    __tablename__ = "album"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    created = db.Column(db.DateTime(timezone=False),
                        default=datetime.datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=False),
                        default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    # TODO tags
    description = db.Column(db.UnicodeText(), nullable=True)
    private = db.Column(db.Boolean(), default=False, nullable=True)
    slug = db.Column(db.String(255), unique=True, nullable=True)

    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    sounds = db.relationship('Sound', backref='album', lazy='dynamic')

    timeline = db.relationship("Timeline", uselist=False,
                               back_populates="album")

    __mapper_args__ = {"order_by": created.desc()}

    def elapsed(self):
        el = datetime.datetime.utcnow() - self.created
        return el.total_seconds()


class Timeline(db.Model):
    __tablename__ = "timeline"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=False),
                          default=datetime.datetime.utcnow)
    private = db.Column(db.Boolean, default=False)

    sound_id = db.Column(db.Integer(), db.ForeignKey('user.id'),
                         nullable=False)
    album_id = db.Column(db.Integer(), db.ForeignKey('album.id'),
                         nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('sound.id'),
                        nullable=False)

    album = db.relationship("Album", back_populates="timeline")
    sound = db.relationship("Sound", back_populates="timeline")

    __mapper_args__ = {"order_by": timestamp.desc()}


licences = {
    0: {"name": "Not Specified", "id": 0, "link": "", "icon": ""},
    1: {"name": "CC Attribution", "id": 1, "link": "https://creativecommons.org/licenses/by/4.0/", "icon": "creative-commons"},
    2: {"name": "CC Attribution Share Alike", "id": 2, "link": "https://creativecommons.org/licenses/by-sa/4.0", "icon": "creative-commons"},
    3: {"name": "CC Attribution No Derivatives", "id": 3, "link": "https://creativecommons.org/licenses/by-nd/4.0", "icon": "creative-commons"},
    4: {"name": "CC Attribution Non Commercial", "id": 4, "link": "https://creativecommons.org/licenses/by-nc/4.0", "icon": "creative-commons"},
    5: {"name": "CC Attribution Non Commercial - Share Alike", "id": 5, "link": "https://creativecommons.org/licenses/by-nc-sa/4.0", "icon": "creative-commons"},
    6: {"name": "CC Attribution Non Commercial - No Derivatives", "id": 6, "link": "https://creativecommons.org/licenses/by-nc-nd/4.0", "icon": "creative-commons"},
    7: {"name": "Public Domain Dedication", "id": 7, "link": "", "icon": ""}
}


@event.listens_for(User, 'after_update')
@event.listens_for(User, 'after_insert')
def make_user_slug(mapper, connection, target):
    if target.slug != "":
        return
    title = "{0} {1}".format(target.id, target.name)
    slug = slugify(title)
    connection.execute(
        User.__table__.update().where(
            User.__table__.c.id == target.id).values(slug=slug)
    )


@event.listens_for(Sound, 'after_update')
@event.listens_for(Sound, 'after_insert')
def make_sound_slug(mapper, connection, target):
    if not target.slug or target.slug == "":
        if not target.title or target.title == "":
            title = "{0} {1}".format(target.id, target.filename)
        else:
            title = "{0} {1}".format(target.id, target.title)
        slug = slugify(title[:255])
        connection.execute(
            Sound.__table__.update().where(
                Sound.__table__.c.id == target.id).values(slug=slug)
        )


@event.listens_for(Album, 'after_update')
@event.listens_for(Album, 'after_insert')
def make_album_slug(mapper, connection, target):
    if not target.slug or target.slug == "":
        title = "{0} {1}".format(target.id, target.title)
        slug = slugify(title[:255])
        connection.execute(
            Album.__table__.update().where(
                Album.__table__.c.id == target.id).values(slug=slug)
        )
