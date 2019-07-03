from flask_security import RegisterForm, current_user
from authlib.flask.oauth2 import current_token
from flask_uploads import UploadSet, AUDIO
from flask_wtf import FlaskForm as Form
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField, SelectField, BooleanField, TextAreaField
from wtforms import widgets
from wtforms.fields.core import StringField
from wtforms.validators import DataRequired, ValidationError, Length, Regexp
from wtforms_alchemy import model_form_factory
from flask_babelex import lazy_gettext
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.csrf.core import CSRFTokenField

from models import db, User, Album, licences

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


class ExtendedRegisterForm(RegisterForm):
    name = StringField(lazy_gettext("Username"), [DataRequired(), Regexp(regex=r"^\w+$"), Length(max=150)])

    def validate_name(form, field):
        if len(field.data) <= 0:
            raise ValidationError(lazy_gettext("Username required"))

        u = db.session.query(User).filter_by(name_insensitive=field.data).first()
        if u:
            raise ValidationError(lazy_gettext("Username already taken"))

    __order = ("name", "email", "password", "password_confirm", "submit")

    def __iter__(self):
        fields = list(super(ExtendedRegisterForm, self).__iter__())
        csrf = any(a.__class__ == CSRFTokenField for a in fields)
        if csrf:
            self.__order += ("csrf_token",)

        get_field = lambda field_id: next((fld for fld in fields if fld.id == field_id))  # noqa: E731
        return (get_field(field_id) for field_id in self.__order)


class UserProfileForm(Form):
    display_name = StringField(lazy_gettext("Display name"), [Length(max=30)])
    timezone = SelectField(coerce=str, label=lazy_gettext("Timezone"), default="UTC")
    locale = SelectField(
        lazy_gettext("Locale"), default="en", choices=[["en", "English"], ["fr", "French"], ["pl", "Polish"]]
    )
    submit = SubmitField(lazy_gettext("Update profile"))


class ConfigForm(Form):
    app_name = StringField(lazy_gettext("Instance Name"), [DataRequired(), Length(max=255)])
    app_description = TextAreaField(lazy_gettext("Instance description"))

    submit = SubmitField(lazy_gettext("Update config"))


def get_albums():
    return Album.query.filter(Album.user_id == current_token.user.id).all()


def get_licences():
    return [(licences[a]["id"], licences[a]["name"]) for a in licences]


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

    def validate_private(form, field):
        if form.album.data:
            if field.data is True and form.album.data.private is False:
                raise ValidationError(lazy_gettext("Cannot put private sound in public album"))

    submit = SubmitField(lazy_gettext("Upload"))


class SoundEditForm(Form):
    title = StringField(lazy_gettext("Title"), [Length(max=255)])
    description = TextAreaField(lazy_gettext("Description"))
    album = QuerySelectField(
        query_factory=get_albums,
        allow_blank=True,
        label=lazy_gettext("Album"),
        blank_text=lazy_gettext("No album"),
        get_label="title",
    )
    licence = SelectField(choices=get_licences(), coerce=int, label=lazy_gettext("Licence"))
    private = BooleanField(lazy_gettext("Private"), default=False)

    def validate_private(form, field):
        if form.album.data:
            if field.data is True and form.album.data.private is False:
                raise ValidationError(lazy_gettext("Cannot put private sound in public album"))
        if field.data is True and form.private.data is False:
            raise ValidationError(lazy_gettext("Published sound cannot be privatized again"))

    submit = SubmitField(lazy_gettext("Edit sound"))


class AlbumForm(Form):
    title = StringField(lazy_gettext("Title"), [Length(max=255), DataRequired()])
    description = TextAreaField(lazy_gettext("Description"))
    private = BooleanField(lazy_gettext("Private"), default=False)

    submit = SubmitField(lazy_gettext("Save"))
