import datetime
from libqth import is_valid_qth

from flask_security import RegisterForm, current_user
from flask_uploads import UploadSet, AUDIO
from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, ValidationError
from wtforms_alchemy import model_form_factory
from wtforms import widgets
from wtforms.fields.core import StringField

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

    password = PasswordField('Password')
    name = StringField('Name')
    email = StringField('Email')
    firstname = StringField('Firstname')
    lastname = StringField('Lastname')
    timezone = SelectField(coerce=str, label='Timezone', default='UTC')
    submit = SubmitField('Update profile')


class ConfigForm(Form):
    app_name = StringField('App Name', [DataRequired()])

    submit = SubmitField('Update config')


class SoundUploadForm(Form):
    title = StringField('Title')
    sound = FileField('File', [FileRequired(), FileAllowed(AUDIO)])
    public = BooleanField('Public', default=True)

    submit = SubmitField('Upload')