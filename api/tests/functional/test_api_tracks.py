from helpers import login, bearerhdr
from werkzeug.datastructures import FileStorage
from models import Sound
import pytest
import os

"""
controllers/api/tracks.py
"""

"""
# TODO

PATCH /api/tracks/<username>/<soundslug>
w/ tags +/- etc., clearing title, etc.

create album; upload track with album; fetch

create album; upload track; fetch; edit add in album; fetch

upload wav; test both file exists locally; remove, test both removed : depends on celery processing

upload user A private; no fetch from user B : depends on celery processing
"""


def test_track_upload(app, client, session, audio_file_mp3, mocker):
    """
    POST /api/tracks
    """
    m = mocker.patch("tasks.upload_workflow.delay")
    audio_file_mp3.seek(0)

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {
        "title": "test track upload",
        "licence": 0,  # unspecified, see api/utils/defaults.py
        "description": "test track upload",
        "file": FileStorage(stream=audio_file_mp3, filename="cat.mp3"),
    }
    # Upload track
    resp = client.post("/api/tracks", data=datas, headers=bearerhdr(access_token), content_type="multipart/form-data")
    assert resp.status_code == 200, resp.data
    assert len(resp.json["id"]) == 36
    assert len(resp.json["slug"]) >= 5
    # Save for later
    track_infos = resp.json

    # Get track informations
    resp = client.get(f"/api/tracks/testusera/{resp.json['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, resp.data
    assert resp.json["account"]["acct"] == "testusera"
    assert isinstance(resp.json["reel2bits"], dict)
    assert resp.json["reel2bits"]["title"] == datas["title"]
    assert resp.json["reel2bits"]["metadatas"]["licence"]["id"] == datas["licence"]
    assert resp.json["content"] == datas["description"]
    assert resp.json["reel2bits"]["private"] is False
    assert resp.json["reel2bits"]["processing"]["transcode_needed"] is False
    assert resp.json["reel2bits"]["processing"]["done"] is False  # the celery workflow isn't ran
    assert len(resp.json["reel2bits"]["media_orig"]) >= 10
    assert len(resp.json["reel2bits"]["media_transcoded"]) >= 10
    assert len(resp.json["reel2bits"]["tags"]) == 0

    # Fetch from database
    sound = Sound.query.filter(Sound.flake_id == track_infos["id"]).one()
    assert sound is not None

    # Assert the celery remoulade
    m.assert_called_once_with(sound.id)

    # Local file should exists
    fpath = os.path.join(app.config["UPLOADED_SOUNDS_DEST"], sound.path_sound(orig=True))
    assert os.path.exists(fpath)


@pytest.mark.parametrize(
    ("title", "description", "tags", "licence"),
    (
        ("testinvalidcombos1", "testinvalidcombos1", "tag1, tag2", 0),
        ("testinvalidcombos2", "", "tag1, tag2", 0),
        ("testinvalidcombos3", "testinvalidcombos3", "", 0),
        ("", "", "", None),
    ),
)
def test_track_upload_invalid_combos(client, session, audio_file_mp3, mocker, title, description, tags, licence):
    """
    POST /api/tracks
    """
    m = mocker.patch("tasks.upload_workflow.delay")
    audio_file_mp3.seek(0)

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {
        "title": title,
        "description": description,
        "file": FileStorage(stream=audio_file_mp3, filename="cat.mp3"),
    }
    if licence:
        datas["licence"] = licence

    # Upload track
    resp = client.post("/api/tracks", data=datas, headers=bearerhdr(access_token), content_type="multipart/form-data")
    if not licence:
        assert resp.status_code == 400, resp.data
        assert "error" in resp.json
        assert "licence" in resp.json["error"]
    else:
        assert resp.status_code == 200, resp.data
        assert len(resp.json["id"]) == 36
        assert len(resp.json["slug"]) >= 5

    if licence:
        # Save for later
        track_infos = resp.json

        # Get track informations
        resp = client.get(f"/api/tracks/testusera/{resp.json['slug']}", headers=bearerhdr(access_token))
        assert resp.status_code == 200, resp.data
        assert resp.json["account"]["acct"] == "testusera"
        assert isinstance(resp.json["reel2bits"], dict)
        assert resp.json["reel2bits"]["metadatas"]["licence"]["id"] == licence
        assert resp.json["content"] == description
        assert resp.json["reel2bits"]["private"] is False
        assert resp.json["reel2bits"]["processing"]["transcode_needed"] is False
        assert resp.json["reel2bits"]["processing"]["done"] is False  # the celery workflow isn't ran
        assert len(resp.json["reel2bits"]["media_orig"]) >= 10
        assert len(resp.json["reel2bits"]["media_transcoded"]) >= 10
        if title == "":
            assert resp.json["reel2bits"]["title"] == "cat.mp3"
        else:
            assert resp.json["reel2bits"]["title"] == title

        # Fetch from database
        sound = Sound.query.filter(Sound.flake_id == track_infos["id"]).one()
        assert sound is not None

        # Assert the celery remoulade
        m.assert_called_once_with(sound.id)


@pytest.mark.parametrize(
    ("tags", "tags_count"), (("", 0), ("tag1, tag2", 2), ("tag1", 1), ("tag1 tag2", 1),),
)
def test_track_upload_with_tags(client, session, audio_file_mp3, mocker, tags, tags_count):
    """
    POST /api/tracks
    """
    m = mocker.patch("tasks.upload_workflow.delay")
    audio_file_mp3.seek(0)

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {
        "title": "testtracktags",
        "description": "testtracktags",
        "file": FileStorage(stream=audio_file_mp3, filename="cat.mp3"),
        "licence": 0,
        "tags": tags,
    }

    # Upload track
    resp = client.post("/api/tracks", data=datas, headers=bearerhdr(access_token), content_type="multipart/form-data")
    assert resp.status_code == 200, resp.data
    assert len(resp.json["id"]) == 36
    assert len(resp.json["slug"]) >= 5

    # Save for later
    track_infos = resp.json

    # Get track informations
    resp = client.get(f"/api/tracks/testusera/{resp.json['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, resp.data
    assert resp.json["account"]["acct"] == "testusera"
    assert isinstance(resp.json["reel2bits"], dict)
    assert resp.json["reel2bits"]["metadatas"]["licence"]["id"] == datas["licence"]
    assert resp.json["content"] == datas["description"]
    assert resp.json["reel2bits"]["private"] is False
    assert resp.json["reel2bits"]["processing"]["transcode_needed"] is False
    assert resp.json["reel2bits"]["processing"]["done"] is False  # the celery workflow isn't ran
    assert len(resp.json["reel2bits"]["media_orig"]) >= 10
    assert len(resp.json["reel2bits"]["media_transcoded"]) >= 10
    assert resp.json["reel2bits"]["title"] == datas["title"]
    assert len(resp.json["reel2bits"]["tags"]) == tags_count
    if tags_count > 0:
        for i in tags.split(","):
            assert i.strip() in resp.json["reel2bits"]["tags"]

    # Fetch from database
    sound = Sound.query.filter(Sound.flake_id == track_infos["id"]).one()
    assert sound is not None

    # Assert the celery remoulade
    m.assert_called_once_with(sound.id)


def test_track_get_invalid(client, session):
    """
    GET /api/tracks/<username_or_id>/<soundslug>
    """
    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # Get track informations
    resp = client.get("/api/tracks/testusera/999-squeak-squeak", headers=bearerhdr(access_token))
    assert resp.status_code == 404, resp.data
    print(resp.json)


def test_track_delete(app, client, session, audio_file_mp3, mocker):
    """
    DELETE /api/tracks/<username>/<soundslug>
    """
    m = mocker.patch("tasks.upload_workflow.delay")
    audio_file_mp3.seek(0)

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {
        "title": "test track delete",
        "licence": 0,  # unspecified, see api/utils/defaults.py
        "description": "test track delete",
        "file": FileStorage(stream=audio_file_mp3, filename="cat.mp3"),
    }
    # Upload track
    resp = client.post("/api/tracks", data=datas, headers=bearerhdr(access_token), content_type="multipart/form-data")
    assert resp.status_code == 200, resp.data
    assert len(resp.json["id"]) == 36
    assert len(resp.json["slug"]) >= 5
    # Save for later
    track_infos = resp.json

    # Get track informations
    resp = client.get(f"/api/tracks/testusera/{resp.json['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, resp.data

    # Fetch from database
    sound = Sound.query.filter(Sound.flake_id == track_infos["id"]).one()
    assert sound is not None

    # Assert the celery remoulade
    m.assert_called_once_with(sound.id)

    # Local file should exists
    fpath = os.path.join(app.config["UPLOADED_SOUNDS_DEST"], sound.path_sound(orig=True))
    assert os.path.exists(fpath)

    # Delete track
    resp = client.delete(f"/api/tracks/testusera/{track_infos['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, resp.data

    # Get track informations
    resp = client.get(f"/api/tracks/testusera/{track_infos['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 404, resp.data

    # File should not exists anymore
    assert not os.path.exists(fpath)


def test_track_delete_other_user(client, session, audio_file_mp3, mocker):
    """
    DELETE /api/tracks/<username>/<soundslug>
    """
    pytest.skip("cannot process from celery so not testable yet")
    m = mocker.patch("tasks.upload_workflow.delay")
    audio_file_mp3.seek(0)

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {
        "title": "test track delete",
        "licence": 0,  # unspecified, see api/utils/defaults.py
        "description": "test track delete",
        "file": FileStorage(stream=audio_file_mp3, filename="cat.mp3"),
    }
    # Upload track
    resp = client.post("/api/tracks", data=datas, headers=bearerhdr(access_token), content_type="multipart/form-data")
    assert resp.status_code == 200, resp.data
    assert len(resp.json["id"]) == 36
    assert len(resp.json["slug"]) >= 5
    # Save for later
    track_infos = resp.json

    # Get track informations
    resp = client.get(f"/api/tracks/testusera/{resp.json['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, resp.data
    assert resp.json["reel2bits"]["private"] is False

    # Fetch from database
    sound = Sound.query.filter(Sound.flake_id == track_infos["id"]).one()
    assert sound is not None

    # Assert the celery remoulade
    m.assert_called_once_with(sound.id)

    # Log as User B
    client_id, client_secret, access_token = login(client, "testuserb", "testuserb")

    # Try to delete track
    resp = client.delete(f"/api/tracks/testusera/{track_infos['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 404, resp.data
    assert resp.json["error"] == "Not found"

    # Get track informations
    resp = client.get(f"/api/tracks/testusera/{track_infos['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, resp.data


def test_track_upload_with_artwork(app, client, session, audio_file_mp3, logo_file, mocker):
    """
    POST /api/tracks
    """
    m = mocker.patch("tasks.upload_workflow.delay")
    audio_file_mp3.seek(0)
    logo_file.seek(0)

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {
        "title": "test track upload",
        "licence": 0,  # unspecified, see api/utils/defaults.py
        "description": "test track upload",
        "file": FileStorage(stream=audio_file_mp3, filename="cat.mp3"),
        "artwork": FileStorage(stream=logo_file, filename="logo.png"),
    }
    # Upload track
    resp = client.post("/api/tracks", data=datas, headers=bearerhdr(access_token), content_type="multipart/form-data")
    assert resp.status_code == 200, resp.data
    assert len(resp.json["id"]) == 36
    assert len(resp.json["slug"]) >= 5
    # Save for later
    track_infos = resp.json

    # Get track informations
    resp = client.get(f"/api/tracks/testusera/{resp.json['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, resp.data
    assert resp.json["reel2bits"]["picture_url"] != "https://localhost.localdomain/static/userpic_placeholder.svg"
    assert resp.json["reel2bits"]["picture_url"].startswith("https://localhost.localdomain/uploads/artwork_sounds/")

    # Fetch from database
    sound = Sound.query.filter(Sound.flake_id == track_infos["id"]).one()
    assert sound is not None

    # Assert the celery remoulade
    m.assert_called_once_with(sound.id)

    # Local audio file should exists
    fpath = os.path.join(app.config["UPLOADED_SOUNDS_DEST"], sound.path_sound(orig=True))
    assert os.path.exists(fpath)

    # Local artwork file should exists
    fpath = os.path.join(app.config["UPLOADED_ARTWORKSOUNDS_DEST"], sound.path_artwork())
    assert os.path.exists(fpath)


def test_track_artwork_update(app, client, session, audio_file_mp3, logo_file, logo_file2, mocker):
    """
    PATCH /api/tracks/<username>/<soundslug>/artwork
    Somehow depends on celery, workaround in place in tasks.py::send_update_sound
    """
    m = mocker.patch("tasks.upload_workflow.delay")
    audio_file_mp3.seek(0)
    logo_file.seek(0)
    logo_file2.seek(0)
    logo_fs = FileStorage(stream=logo_file, filename="logo.png")
    logo_fs2 = FileStorage(stream=logo_file2, filename="logo.png")

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {
        "title": "test track upload",
        "licence": 0,  # unspecified, see api/utils/defaults.py
        "description": "test track upload",
        "file": FileStorage(stream=audio_file_mp3, filename="cat.mp3"),
        "artwork": logo_fs,
    }
    # Upload track
    resp = client.post("/api/tracks", data=datas, headers=bearerhdr(access_token), content_type="multipart/form-data")
    assert resp.status_code == 200, resp.data
    assert len(resp.json["id"]) == 36
    assert len(resp.json["slug"]) >= 5
    # Save for later
    track_infos = resp.json

    # Get track informations
    resp = client.get(f"/api/tracks/testusera/{track_infos['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, resp.data
    assert resp.json["reel2bits"]["picture_url"] != "https://localhost.localdomain/static/userpic_placeholder.svg"
    assert resp.json["reel2bits"]["picture_url"].startswith("https://localhost.localdomain/uploads/artwork_sounds/")
    orig_picture_url = resp.json["reel2bits"]["picture_url"]

    # Fetch from database
    sound = Sound.query.filter(Sound.flake_id == track_infos["id"]).one()
    assert sound is not None

    # Assert the celery remoulade
    m.assert_called_once_with(sound.id)

    # Local audio file should exists
    fpath = os.path.join(app.config["UPLOADED_SOUNDS_DEST"], sound.path_sound(orig=True))
    assert os.path.exists(fpath)

    # Local artwork file should exists
    fpath = os.path.join(app.config["UPLOADED_ARTWORKSOUNDS_DEST"], sound.path_artwork())
    assert os.path.exists(fpath)

    # "change" the artwork
    datas = {"artwork": logo_fs2}
    resp = client.patch(
        f"/api/tracks/testusera/{track_infos['slug']}/artwork",
        data=datas,
        headers=bearerhdr(access_token),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200, resp.data
    assert resp.json["status"] == "ok"
    assert not orig_picture_url.endswith(resp.json["path"])

    # Check old and new files
    newfpath = os.path.join(app.config["UPLOADED_ARTWORKSOUNDS_DEST"], resp.json["path"])
    assert os.path.exists(newfpath)
    assert newfpath != fpath
    assert not os.path.exists(fpath)
