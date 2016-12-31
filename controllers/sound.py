import pytz
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_security import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename
from forms import SoundUploadForm
from models import db, User, UserLogging, Sound
from flask_uploads import UploadSet, AUDIO

bp_sound = Blueprint('bp_sound', __name__)

sounds = UploadSet('sounds', AUDIO)


@bp_sound.route('/sound/upload', methods=['GET', 'POST'])
@login_required
def upload():
    pcfg = {"title": "New upload"}

    form = SoundUploadForm()

    if request.method == 'POST' and 'sound' in request.files:
        if form.validate_on_submit():
            filename = sounds.save(request.files['sound'])
            rec = Sound()
            rec.filename=filename
            rec.user_id=current_user.id
            rec.title = form.title.data
            rec.public = form.public.data

            db.session.add(rec)
            db.session.commit()
            flash('Uploaded !', 'success')
        else:
            return render_template('sound/upload.jinja2', pcfg=pcfg, form=form, flash='Error with the file')
        return redirect(url_for('bp_main.home', username=current_user.name))
        # TODO redirect to song page

    # GET
    return render_template('sound/upload.jinja2', pcfg=pcfg, form=form)