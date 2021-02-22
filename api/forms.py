from authlib.integrations.flask_oauth2 import current_token
from flask_uploads import UploadSet, AUDIO
from flask_wtf import FlaskForm as Form
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField, SelectField, BooleanField, TextAreaField
from wtforms import widgets
from wtforms.fields.core import StringField
from wtforms.validators import DataRequired, ValidationError, Length
from wtforms_alchemy import model_form_factory
from flask_babelex import lazy_gettext
from wtforms_alchemy.fields import QuerySelectField

from models import db, Album
from utils.defaults import Reel2bitsDefaults

BaseModelForm = model_form_factory(Form)

sounds = UploadSet("sounds", AUDIO)


class PasswordFieldNotHidden(StringField):
    """
    Original source: https://github.com/wtforms/wtforms/blob/2.0.2/wtforms/fields/simple.py#L35-L42  # noqa: E501

    A StringField, except renders an ``<input type="password">``.
    Also, whatever value is accepted by this field is not rendered back
    to the browser like normal fields.
    """

    widget = widgets.PasswordInput(hide_value=False)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(cls):
        return db.session


class ConfigForm(Form):
    app_name = StringField(lazy_gettext("Instance Name"), [DataRequired(), Length(max=255)])
    app_description = TextAreaField(lazy_gettext("Instance description"))
    announcement = TextAreaField(lazy_gettext("Instance announcement"))

    submit = SubmitField(lazy_gettext("Update config"))


def get_albums():
    return Album.query.filter(Album.user_id == current_token.user.id).all()


def get_licences():
    return [
        (Reel2bitsDefaults.known_licences[a]["id"], Reel2bitsDefaults.known_licences[a]["name"])
        for a in Reel2bitsDefaults.known_licences
    ]


class SoundUploadForm(Form):
    title = StringField(lazy_gettext("Title"), [Length(max=255)])
    description = TextAreaField(lazy_gettext("Description"))
    file = FileField(lazy_gettext("File"), [FileRequired(), FileAllowed(AUDIO)])
    album = QuerySelectField(
        query_factory=get_albums,
        allow_blank=True,
        label=lazy_gettext("Album"),
        blank_text=lazy_gettext("No album"),
        get_label="title",
    )
    licence = SelectField(choices=get_licences(), coerce=int, label=lazy_gettext("Licence"))
    private = BooleanField(lazy_gettext("Private"), default=False)
    genre = StringField("Genre", [Length(max=255)])
    tags = StringField("Tags", [Length(max=1000)])

    def validate_private(form, field):
        if form.album.data:
            if field.data is True and form.album.data.private is False:
                raise ValidationError(lazy_gettext("Cannot put private sound in public album"))

    submit = SubmitField(lazy_gettext("Upload"))


class AlbumForm(Form):
    title = StringField(lazy_gettext("Title"), [Length(max=255), DataRequired()])
    description = TextAreaField(lazy_gettext("Description"))
    private = BooleanField(lazy_gettext("Private"), default=False)
    genre = StringField("Genre", [Length(max=255)])
    tags = StringField("Tags", [Length(max=1000)])

    submit = SubmitField(lazy_gettext("Save"))
