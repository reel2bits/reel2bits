import datetime
import os

from flask_security import SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from slugify import slugify
from sqlalchemy import event
from sqlalchemy.sql import func
from sqlalchemy_searchable import make_searchable, SearchQueryMixin

db = SQLAlchemy()
make_searchable()


class LogQuery(BaseQuery, SearchQueryMixin):
    pass


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, info={'label': 'Name'})
    description = db.Column(db.String(255), info={'label': 'Description'})

    __mapper_args__ = {"order_by": name}


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, info={'label': 'Email'})
    name = db.Column(db.String(255), unique=True, nullable=False, info={'label': 'Name'})
    password = db.Column(db.String(255), nullable=False, info={'label': 'Password'})
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())

    firstname = db.Column(db.String(32))
    lastname = db.Column(db.String(32))

    timezone = db.Column(db.String(255), nullable=False, default='UTC')  # Managed and fed by pytz

    slug = db.Column(db.String(255), unique=True, nullable=True)

    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    apitokens = db.relationship('Apitoken', backref='user', lazy='dynamic', cascade="delete")

    user_loggings = db.relationship('UserLogging', backref='user', lazy='dynamic', cascade="delete")
    loggings = db.relationship('Logging', backref='user', lazy='dynamic', cascade="delete")

    sounds = db.relationship('Sound', backref='user', lazy='dynamic', cascade="delete")

    __mapper_args__ = {"order_by": name}

    def join_roles(self, string):
        return string.join([i.description for i in self.roles])


class Apitoken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, info={'label': 'Token'})
    secret = db.Column(db.String(255), unique=True, nullable=False, info={'label': 'Secret'})


user_datastore = SQLAlchemyUserDatastore(db, User, Role)


class Config(db.Model):
    __tablename__ = "config"

    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(255), default=None)


class Logging(db.Model):
    __tablename__ = "logging"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255), nullable=False, default="General")
    level = db.Column(db.String(255), nullable=False, default="INFO")
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=True)


class UserLogging(db.Model):
    __tablename__ = "user_logging"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255), nullable=False, default="General")
    level = db.Column(db.String(255), nullable=False, default="INFO")
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)


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

    sound_id = db.Column(db.Integer(), db.ForeignKey('sound.id'), nullable=False)


class Sound(db.Model):
    __tablename__ = "sound"

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
    description = db.Column(db.UnicodeText(), nullable=True)
    private = db.Column(db.Boolean(), default=False, nullable=True)
    slug = db.Column(db.String(255), unique=True, nullable=True)
    filename = db.Column(db.String(255), unique=False, nullable=True)
    filename_orig = db.Column(db.String(255), unique=False, nullable=True)

    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    sound_infos = db.relationship('SoundInfo', backref='sound_info', lazy='dynamic', cascade="delete")

    def elapsed(self):
        print("db: {0}, now: {1}".format(self.uploaded, datetime.datetime.utcnow()))
        el = datetime.datetime.utcnow() - self.uploaded
        return el.total_seconds()

    def path_waveform(self):
        return os.path.join(self.user.slug, "{0}.png".format(self.filename))

    def path_sound(self):
        return os.path.join(self.user.slug, self.filename)


@event.listens_for(User, 'after_update')
@event.listens_for(User, 'after_insert')
def make_user_slug(mapper, connection, target):
    if target.slug != "":
        return
    title = "{0} {1}".format(target.id, target.name)
    slug = slugify(title)
    connection.execute(
        User.__table__.update().where(User.__table__.c.id == target.id).values(slug=slug)
    )


@event.listens_for(Sound, 'after_update')
@event.listens_for(Sound, 'after_insert')
def make_sound_slug(mapper, connection, target):
    if not target.slug or target.slug == "":
        if not target.title or target.title == "":
            title = "{0} {1}".format(target.id, target.filename)
        else:
            title = "{0} {1}".format(target.id, target.title)
        slug = slugify(title)
        connection.execute(
            Sound.__table__.update().where(Sound.__table__.c.id == target.id).values(slug=slug)
        )
