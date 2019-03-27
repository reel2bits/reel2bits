from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort, json
from flask_babelex import gettext
from flask_security import login_required, current_user
from flask_uploads import UploadSet, AUDIO
from little_boxes import activitypub as ap

from forms import SoundUploadForm, SoundEditForm
from models import db, User, Sound
from utils import get_hashed_filename, InvalidUsage, add_user_log
from tasks import send_update_sound

bp_sound = Blueprint("bp_sound", __name__)

sounds = UploadSet("sounds", AUDIO)


@bp_sound.route("/user/<string:username>/track/<string:soundslug>", methods=["GET"])
def show(username, soundslug):
    user = User.query.filter(User.name == username).first()
    if not user:
        flash(gettext("User not found"), "error")
        return redirect(url_for("bp_main.home"))
    if current_user.is_authenticated and user.id == current_user.id:
        sound = Sound.query.filter(Sound.slug == soundslug, Sound.user_id == user.id).first()
    else:
        sound = Sound.query.filter(
            Sound.slug == soundslug, Sound.user_id == user.id, Sound.transcode_state == Sound.TRANSCODE_DONE
        ).first()

    if not sound:
        flash(gettext("Sound not found"), "error")
        return redirect(url_for("bp_users.profile", name=user.name))

    if sound.private:
        if current_user.is_authenticated:
            if sound.user_id != current_user.id:
                flash(gettext("Sound not found"), "error")
                return redirect(url_for("bp_users.profile", name=user.name))
        else:
            flash(gettext("Sound not found"), "error")
            return redirect(url_for("bp_users.profile", name=user.name))

    pcfg = {"title": sound.title}

    si = sound.sound_infos.first()
    if si:
        si_w = si.waveform
    else:
        si_w = None

    # if si and si.type == "FLAC":
    #    flash(gettext("No HTML5 player supported actually"), 'info')

    return render_template("sound/show.jinja2", pcfg=pcfg, user=user, sound=sound, waveform=si_w)


@bp_sound.route("/user/<string:username>/track/<string:soundslug>/waveform.json", methods=["GET"])
def waveform_json(username, soundslug):
    user = User.query.filter(User.name == username).first()
    if not user:
        raise InvalidUsage("User not found", status_code=404)
    sound = Sound.query.filter(Sound.slug == soundslug, Sound.user_id == user.id).first()
    if not sound:
        raise InvalidUsage("Sound not found", status_code=404)

    if sound.private:
        if current_user:
            if sound.user_id != current_user.id:
                raise InvalidUsage("Sound not found", status_code=404)
        else:
            raise InvalidUsage("Sound not found", status_code=404)

    si = sound.sound_infos.first()
    if not si:
        return abort(404)
    wf = json.loads(si.waveform)
    wf["filename"] = sound.path_sound()
    wf["wf_png"] = sound.path_waveform()
    wf["title"] = sound.title
    return Response(json.dumps(wf), mimetype="application/json;charset=utf-8")


@bp_sound.route("/sound/upload", methods=["GET", "POST"])
@login_required
def upload():
    pcfg = {"title": gettext("New upload")}
    user = User.query.filter(User.id == current_user.id).one()

    form = SoundUploadForm()

    if request.method == "POST" and "sound" in request.files:
        if form.validate_on_submit():
            filename_orig = request.files["sound"].filename
            filename_hashed = get_hashed_filename(filename_orig)

            sounds.save(request.files["sound"], folder=user.slug, name=filename_hashed)

            rec = Sound()
            rec.filename = filename_hashed
            rec.filename_orig = filename_orig
            rec.licence = form.licence.data
            if form.album.data:
                rec.album_id = form.album.data.id
                if not form.album.data.sounds:
                    rec.album_order = 0
                else:
                    rec.album_order = form.album.data.sounds.count() + 1

            rec.user_id = current_user.id
            if not form.title.data:
                rec.title = filename_orig
            else:
                rec.title = form.title.data
            rec.private = form.private.data

            if "flac" in request.files["sound"].mimetype or "ogg" in request.files["sound"].mimetype:
                rec.transcode_state = Sound.TRANSCODE_WAITING
                rec.transcode_needed = True

            db.session.add(rec)
            db.session.commit()

            # push the job in queue
            from tasks import upload_workflow

            upload_workflow.delay(rec.id)

            # log
            add_user_log(rec.id, user.id, "sounds", "info", "Uploaded {0} -- {1}".format(rec.id, rec.title))

            flash(gettext("Uploaded ! Processing will now follow."), "success")
        else:
            return render_template("sound/upload.jinja2", pcfg=pcfg, form=form, flash="Error with the file")
        return redirect(url_for("bp_sound.show", username=current_user.name, soundslug=rec.slug))

    # GET
    return render_template("sound/upload.jinja2", pcfg=pcfg, form=form)


@bp_sound.route("/user/<string:username>/track/<string:soundslug>/edit", methods=["GET", "POST"])
@login_required
def edit(username, soundslug):
    sound = Sound.query.filter(Sound.user_id == current_user.id, Sound.slug == soundslug).first()
    if not sound:
        flash(gettext("Sound not found"), "error")
        return redirect(url_for("bp_users.profile", name=username))

    if sound.user.id != current_user.id:
        flash(gettext("Forbidden"), "error")
        return redirect(url_for("bp_users.profile", name=username))

    pcfg = {"title": gettext("Edit %(title)s", title=sound.title)}

    form = SoundEditForm(request.form, obj=sound)

    if form.validate_on_submit():
        sound.title = form.title.data
        sound.private = form.private.data
        sound.description = form.description.data
        sound.licence = form.licence.data
        if form.album.data:
            sound.album_id = form.album.data.id
            if not sound.album_order:
                if not form.album.data.sounds:
                    sound.album_order = 0
                else:
                    sound.album_order = form.album.data.sounds.count() + 1

        db.session.commit()
        # log
        add_user_log(sound.id, sound.user.id, "sounds", "info", "Edited {0} -- {1}".format(sound.id, sound.title))
        # trigger a sound update
        send_update_sound(sound)
        return redirect(url_for("bp_sound.show", username=username, soundslug=sound.slug))

    return render_template("sound/edit.jinja2", pcfg=pcfg, form=form, sound=sound)


@bp_sound.route("/user/<string:username>/track/<string:soundslug>/delete", methods=["GET", "DELETE", "PUT"])
@login_required
def delete(username, soundslug):
    sound = Sound.query.filter(Sound.user_id == current_user.id, Sound.slug == soundslug).first()
    if not sound:
        flash(gettext("Sound not found"), "error")
        return redirect(url_for("bp_users.profile", name=username))

    if sound.user.id != current_user.id:
        flash(gettext("Forbidden"), "error")
        return redirect(url_for("bp_users.profile", name=username))

    # Federate Delete
    # TODO: Test
    from tasks import post_to_outbox

    activity = sound.activity
    delete_activity = ap.Delete(actor=sound.user.actor[0], object=ap.Tombstone(id=activity.id).to_dict(embed=True))
    post_to_outbox(delete_activity)

    db.session.delete(sound)
    db.session.commit()

    # log
    add_user_log(sound.id, sound.user.id, "sounds", "info", "Deleted {0} -- {1}".format(sound.id, sound.title))

    return redirect(url_for("bp_users.profile", name=username))
