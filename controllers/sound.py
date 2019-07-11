from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort, json
from flask_babelex import gettext
from flask_security import login_required, current_user
from flask_uploads import UploadSet, AUDIO

from forms import SoundEditForm
from models import db, User, Sound
from utils import InvalidUsage, add_user_log

bp_sound = Blueprint("bp_sound", __name__)

sounds = UploadSet("sounds", AUDIO)


# TODO (dashie), might also get implemented into the new API
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

    federate_new = False

    if form.validate_on_submit():
        if sound.private and not form.private.data:
            # Switched to public
            federate_new = True
            sound.private = form.private.data

        if not sound.private and form.private.data:
            # Can't switch back to private
            sound.private = False

        sound.title = form.title.data
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

        if federate_new:
            # Switched from private to public: initial federation

            from tasks import federate_new_sound

            sound.activity_id = federate_new_sound(sound)
            db.session.commit()

        else:
            # it's an update
            from tasks import send_update_sound

            send_update_sound(sound)

        return redirect(url_for("bp_sound.show", username=username, soundslug=sound.slug))
    else:
        form.private.data = sound.private

    if not sound.private:
        del form.private

    return render_template("sound/edit.jinja2", pcfg=pcfg, form=form, sound=sound)
