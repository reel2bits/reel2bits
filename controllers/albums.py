from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, json
from flask_security import login_required, current_user
from flask_babel import lazy_gettext, gettext

from forms import AlbumForm
from models import db, User, Album, Sound
from utils import InvalidUsage

bp_albums = Blueprint('bp_albums', __name__)


@bp_albums.route('/user/<string:username>/sets/new', methods=['GET', 'POST'])
@login_required
def new(username):
    pcfg = {"title": lazy_gettext("New album")}

    form = AlbumForm()

    if form.validate_on_submit():
        rec = Album()
        rec.user_id = current_user.id
        rec.title = form.title.data
        rec.private = form.private.data
        rec.description = form.description.data

        db.session.add(rec)
        db.session.commit()
        flash(lazy_gettext('Created !'), 'success')
    else:
        return render_template('album/new.jinja2', pcfg=pcfg, form=form)
    return redirect(url_for('bp_albums.show', username=current_user.name, setslug=rec.slug))


@bp_albums.route('/user/<string:username>/sets/<string:setslug>', methods=['GET'])
def show(username, setslug):
    user = User.query.filter(User.name == username).first()
    if not user:
        flash(lazy_gettext("User not found"), "error")
        return redirect(url_for("bp_main.home"))
    album = Album.query.filter(Album.slug == setslug, Album.user_id == user.id).first()
    if not album:
        flash(lazy_gettext("Album not found"), "error")
        return redirect(url_for("bp_users.profile", name=user.name))

    if album.private:
        if current_user.is_authenticated:
            if album.user_id != current_user.id:
                flash(lazy_gettext("Album not found"), "error")
                return redirect(url_for("bp_users.profile", name=user.name))
        else:
            flash(lazy_gettext("Album not found"), "error")
            return redirect(url_for("bp_users.profile", name=user.name))

    pcfg = {"title": album.title}

    return render_template('album/show.jinja2', pcfg=pcfg, user=user,
                           album=album, sound=album.sounds.order_by('album_order asc').first())


@bp_albums.route('/user/<string:username>/sets/<string:setslug>/edit', methods=['GET', 'POST'])
@login_required
def edit(username, setslug):
    album = Album.query.filter(Album.user_id == current_user.id, Album.slug == setslug).first()
    if not album:
        flash(lazy_gettext("Album not found"), 'error')
        return redirect(url_for('bp_users.profile', name=username))

    pcfg = {"title": gettext(u'Edit %(value)s', value=album.title)}

    form = AlbumForm(request.form, album)

    contains_private = False
    if album.sounds and form.private.data is False:
        for sound in album.sounds:
            if form.private.data is False and sound.private is True:
                contains_private = True

    if not contains_private:
        if form.validate_on_submit():
            album.title = form.title.data
            album.private = form.private.data
            album.description = form.description.data

            db.session.commit()
            return redirect(url_for('bp_albums.show', username=username, setslug=album.slug))
    else:
        flash(lazy_gettext("Public album cannot have private sounds"), "error")
    return render_template('album/edit.jinja2', pcfg=pcfg, form=form, album=album)


@bp_albums.route('/user/<string:username>/sets/<string:setslug>/delete', methods=['GET', 'DELETE', 'PUT'])
@login_required
def delete(username, setslug):
    album = Album.query.filter(Album.user_id == current_user.id, Album.slug == setslug).first()
    if not album:
        flash(lazy_gettext("Album not found"), 'error')
        return redirect(url_for('bp_users.profile', name=username))

    db.session.delete(album)
    db.session.commit()

    return redirect(url_for('bp_users.profile', name=username))


@bp_albums.route('/user/<string:username>/sets/<string:setslug>/reorder.json', methods=['POST'])
def reorder_json(username, setslug):
    user = User.query.filter(User.name == username).first()
    if not user:
        flash(lazy_gettext("User not found"), "error")
        return redirect(url_for("bp_main.home"))
    album = Album.query.filter(Album.slug == setslug, Album.user_id == user.id).first()
    if not album:
        raise InvalidUsage('Album not found', status_code=404)

    if album.private:
        if current_user:
            if album.user_id != current_user.id:
                raise InvalidUsage('Album not found', status_code=404)
        else:
            raise InvalidUsage('Album not found', status_code=404)

    moved = []

    if not request.get_json():
        raise InvalidUsage('Invalid json', status_code=500)

    for snd in request.get_json()['data']:
        sound = Sound.query.filter(Sound.id == int(snd['soundid']), Sound.album_id == album.id).first()
        if not sound:
            raise InvalidUsage('Sound not found', status_code=404)

        if sound.album_order != int(snd['oldPosition']):
            raise InvalidUsage("Old position %s doesn't match bdd one %s" % (int(snd['oldPosition']),
                                                                             sound.album_order))
        sound.album_order = int(snd['newPosition'])

        moved.append(sound.id)

    db.session.commit()

    datas = {'status': 'ok', 'moved': moved}

    return Response(json.dumps(datas), mimetype='application/json;charset=utf-8')
