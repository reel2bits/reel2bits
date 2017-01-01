from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort, json
from flask_security import login_required, current_user
from flask_uploads import UploadSet, AUDIO

from forms import SoundUploadForm, SoundEditForm
from models import db, User, Sound
from utils import get_hashed_filename

bp_sound = Blueprint('bp_sound', __name__)

sounds = UploadSet('sounds', AUDIO)


@bp_sound.route('/user/<string:username>/<string:soundslug>', methods=['GET'])
def show(username, soundslug):
    user = User.query.filter(User.name == username).first()
    if not user:
        flash("User not found", "error")
        return redirect(url_for("bp_main.home"))
    sound = Sound.query.filter(Sound.slug == soundslug, Sound.user_id == user.id).first()
    if not sound:
        flash("Sound not found", "error")
        return redirect(url_for("bp_users.profile", name=user.name))

    if sound.private:
        if current_user.is_authenticated:
            if sound.user_id != current_user.id:
                flash("Sound not found", "error")
                return redirect(url_for("bp_users.profile", name=user.name))
        else:
            flash("Sound not found", "error")
            return redirect(url_for("bp_users.profile", name=user.name))

    pcfg = {"title": sound.title}

    si = sound.sound_infos.first()
    if si:
        si_w = si.waveform
    else:
        si_w = None

    if si and si.type == "FLAC":
        flash("No HTML5 player supported actually", 'info')

    return render_template('sound/show.jinja2', pcfg=pcfg, user=user, sound=sound, waveform=si_w)


@bp_sound.route('/user/<string:username>/<string:soundslug>/waveform.json', methods=['GET'])
def waveform_json(username, soundslug):
    user = User.query.filter(User.name == username).first()
    if not user:
        flash("User not found", "error")
        return redirect(url_for("bp_main.home"))
    sound = Sound.query.filter(Sound.slug == soundslug, Sound.user_id == user.id).first()
    if not sound:
        flash("Sound not found", "error")
        return redirect(url_for("bp_users.profile", user=user.name))

    if sound.private:
        if current_user:
            if sound.user_id != current_user.id:
                flash("Sound not found", "error")
                return redirect(url_for("bp_users.profile", user=user.name))
        else:
            flash("Sound not found", "error")
            return redirect(url_for("bp_users.profile", user=user.name))

    si = sound.sound_infos.first()
    if not si:
        return abort(404)
    wf = json.loads(si.waveform)
    return Response(json.dumps(wf['data']), mimetype='application/json;charset=utf-8')


@bp_sound.route('/sound/upload', methods=['GET', 'POST'])
@login_required
def upload():
    pcfg = {"title": "New upload"}
    user = User.query.filter(User.id == current_user.id).one()

    form = SoundUploadForm()

    if request.method == 'POST' and 'sound' in request.files:
        if form.validate_on_submit():
            filename_orig = request.files['sound'].filename
            filename_hashed = get_hashed_filename(filename_orig)

            sounds.save(request.files['sound'], folder=user.slug, name=filename_hashed)

            rec = Sound()
            rec.filename = filename_hashed
            rec.filename_orig = filename_orig

            rec.user_id = current_user.id
            if not form.title.data:
                rec.title = filename_orig
            else:
                rec.title = form.title.data
            rec.private = form.private.data

            db.session.add(rec)
            db.session.commit()
            flash('Uploaded !', 'success')
        else:
            return render_template('sound/upload.jinja2', pcfg=pcfg, form=form, flash='Error with the file')
        return redirect(url_for('bp_sound.show', username=current_user.name, soundslug=rec.slug))

    # GET
    return render_template('sound/upload.jinja2', pcfg=pcfg, form=form)


@bp_sound.route('/user/<string:username>/<string:soundslug>/edit', methods=['GET', 'POST'])
@login_required
def edit(username, soundslug):
    sound = Sound.query.filter(Sound.user_id == current_user.id, Sound.slug == soundslug).first()
    if not sound:
        flash("Sound not found", 'error')
        return redirect(url_for('bp_users.profile', name=username))

    pcfg = {"title": "Edit {0}".format(sound.title)}

    form = SoundEditForm(request.form, sound)

    if form.validate_on_submit():
        sound.title = form.title.data
        sound.private = form.private.data
        sound.description = form.description.data

        db.session.commit()
        return redirect(url_for('bp_sound.show', username=username, soundslug=sound.slug))

    return render_template('sound/edit.jinja2', pcfg=pcfg, form=form, sound=sound)


@bp_sound.route('/user/<string:username>/<string:soundslug>/delete', methods=['GET', 'DELETE', 'PUT'])
@login_required
def delete(username, soundslug):
    sound = Sound.query.filter(Sound.user_id == current_user.id, Sound.slug == soundslug).first()
    if not sound:
        flash("Sound not found", 'error')
        return redirect(url_for('bp_users.profile', name=username))

    db.session.delete(sound)
    db.session.commit()

    return redirect(url_for('bp_users.profile', name=username))
