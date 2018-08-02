from flask_security import RegisterForm, current_user
from flask_uploads import UploadSet, AUDIO
from flask_wtf import FlaskForm as Form
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import PasswordField, SubmitField, SelectField,\
    BooleanField, TextAreaField
from wtforms import widgets
from wtforms.fields.core import StringField
from wtforms.validators import DataRequired, ValidationError, \
    Length, Regexp
from wtforms_alchemy import model_form_factory
from flask_babelex import gettext
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from models import db, User, Album, licences

BaseModelForm = model_form_factory(Form)

sounds = UploadSet('sounds', AUDIO)


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
    name = StringField('Username', [DataRequired(),
                                    Regexp(regex='^\w+$'),
                                    Length(max=150)])

    def validate_name(form, field):
        if len(field.data) <= 0:
            raise ValidationError(gettext("Username required"))

        u = db.session.query(User).filter_by(
            name_insensitive=field.data).first()
        if u:
            raise ValidationError(gettext("Username already taken"))


class UserProfileForm(ModelForm):
    class Meta:
        model = User

    password = PasswordField(gettext('Password'), [Length(max=255)])
    name = StringField(gettext('Name'), [Length(max=255)])
    email = StringField(gettext('Email'), [Length(max=255)])
    firstname = StringField(gettext('Firstname'), [Length(max=32)])
    lastname = StringField(gettext('Lastname'), [Length(max=32)])
    timezone = SelectField(coerce=str, label=gettext('Timezone'),
                           default='UTC')
    locale = SelectField(gettext('Locale'), default="en",
                         choices=[['en', 'English'], ['fr', 'French']])
    submit = SubmitField(gettext('Update profile'))


class ConfigForm(Form):
    app_name = StringField(
        gettext('Instance Name'), [DataRequired(), Length(max=255)])
    app_description = TextAreaField(gettext('Instance description'))

    submit = SubmitField(gettext('Update config'))


def get_albums():
    return Album.query.filter(Album.user_id == current_user.id).all()


def get_licences():
    return [(licences[a]['id'], licences[a]['name']) for a in licences]


class SoundUploadForm(Form):
    title = StringField(gettext('Title'), [Length(max=255)])
    sound = FileField(gettext('File'), [FileRequired(),
                                        FileAllowed(AUDIO)])
    private = BooleanField(gettext('Private'), default=False)
    album = QuerySelectField(query_factory=get_albums,
                             allow_blank=True,
                             label=gettext('Album'),
                             blank_text=gettext('No album'),
                             get_label='title')
    licence = SelectField(choices=get_licences(),
                          coerce=int,
                          label=gettext('Licence'))

    def validate_private(form, field):
        if field.data is True and form.album.data.private is False:
            raise ValidationError(
                gettext("Cannot put private sound in public album"))

    submit = SubmitField(gettext('Upload'))


class SoundEditForm(Form):
    title = StringField(gettext('Title'), [Length(max=255)])
    private = BooleanField(gettext('Private'), default=False)
    description = TextAreaField(gettext('Description'))
    album = QuerySelectField(query_factory=get_albums,
                             allow_blank=True,
                             label=gettext('Album'),
                             blank_text=gettext('No album'),
                             get_label='title')
    licence = SelectField(choices=get_licences(),
                          coerce=int,
                          label=gettext('Licence'))

    def validate_private(form, field):
        if field.data is True and form.album.data.private is False:
            raise ValidationError(
                gettext("Cannot put private sound in public album"))

    submit = SubmitField(gettext('Edit sound'))


class AlbumForm(Form):
    title = StringField(gettext('Title'), [Length(max=255),
                                           DataRequired()])
    description = TextAreaField(gettext('Description'))
    private = BooleanField(gettext('Private'), default=False)

    submit = SubmitField(gettext('Save'))
