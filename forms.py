from flask_security import RegisterForm
from flask_uploads import UploadSet, AUDIO
from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import PasswordField, SubmitField, SelectField, BooleanField, TextAreaField
from wtforms import widgets
from wtforms.fields.core import StringField
from wtforms.validators import DataRequired, ValidationError, Length
from wtforms_alchemy import model_form_factory

from models import db, User

BaseModelForm = model_form_factory(Form)

sounds = UploadSet('sounds', AUDIO)


class PasswordFieldNotHidden(StringField):
    """
    Original source: https://github.com/wtforms/wtforms/blob/2.0.2/wtforms/fields/simple.py#L35-L42

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
    name = StringField('Name', [DataRequired()])

    def validate_name(form, field):
        if len(field.data) <= 0:
            raise ValidationError("Username required")

        u = User.query.filter(User.name == field.data).first()
        if u:
            raise ValidationError("Username already taken")


class UserProfileForm(ModelForm):
    class Meta:
        model = User

    password = PasswordField('Password', [Length(min=10, max=255)])
    name = StringField('Name', [Length(max=255)])
    email = StringField('Email', [Length(max=255)])
    firstname = StringField('Firstname', [Length(max=32)])
    lastname = StringField('Lastname', [Length(max=32)])
    timezone = SelectField(coerce=str, label='Timezone', default='UTC')
    submit = SubmitField('Update profile')


class ConfigForm(Form):
    app_name = StringField('App Name', [DataRequired(), Length(max=255)])

    submit = SubmitField('Update config')


class SoundUploadForm(Form):
    title = StringField('Title', [Length(max=255)])
    sound = FileField('File', [FileRequired(), FileAllowed(AUDIO)])
    private = BooleanField('Private', default=False)

    submit = SubmitField('Upload')


class SoundEditForm(Form):
    title = StringField('Title', [Length(max=255)])
    private = BooleanField('Private', default=False)
    description = TextAreaField('Description')

    submit = SubmitField('Upload')
