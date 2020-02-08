from helpers import bearerhdr, headers, login
import pytest
from models import User

"""
controllers/api/albums.py
"""

"""
# TODO all of that
PATCH /api/albums/<username>/<albumslug>/reorder

PATCH /api/albums/<username>/<albumslug>/artwork
"""


@pytest.mark.parametrize(
    ("title", "private", "description", "genre", "tags", "is_valid"),
    (
        ("A random album", False, "Some description", "Hard potat", "potat, squished", True),
        ("A random album 2", True, "", "", "", True),
        ("A random album 3", False, "", "", "", True),
        ("A random album 4", False, "Description", "", "potat", True),
        ("", False, "", "", "", False),
    ),
)
def test_albums_new(client, session, title, private, description, genre, tags, is_valid):
    """
    POST /api/albums
    """

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {"title": title, "description": description, "genre": genre, "tags": tags}
    if private:
        datas["private"] = True

    resp = client.post("/api/albums", data=datas, headers=bearerhdr(access_token))
    if is_valid:
        assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
        assert "id" in resp.json, f"{resp.status_code} - {resp.data!r}"
        assert "slug" in resp.json, f"{resp.status_code} - {resp.data!r}"
    else:
        assert resp.status_code == 400, f"{resp.status_code} - {resp.data!r}"
        assert "error" in resp.json, f"{resp.status_code} - {resp.data!r}"


def test_albums_get(client, session):
    """
    GET /api/albums/<username_or_id>/<albumslug>
    """

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {"title": "testalbumget", "private": False, "description": "squeak", "genre": "", "tags": ""}

    resp = client.post("/api/albums", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert "id" in resp.json, f"{resp.status_code} - {resp.data!r}"
    assert "slug" in resp.json, f"{resp.status_code} - {resp.data!r}"

    # Get album
    resp = client.get(f"/api/albums/testusera/{resp.json['slug']}", headers=bearerhdr(access_token))
    assert resp.status_code == 200
    assert resp.json["reel2bits"]["title"] == "testalbumget"
    assert resp.json["content"] == "squeak"
    assert resp.json["account"]["username"] == "testusera"


def test_albums_get_not_found(client, session):
    """
    GET /api/albums/<username_or_id>/<albumslug>
    """
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # Get album
    resp = client.get("/api/albums/testuserb/thisalbumdoesnotexist", headers=bearerhdr(access_token))
    assert resp.status_code == 404


@pytest.mark.parametrize(
    ("title", "private", "username", "username_against"),
    (
        ("A random public album 1", False, "testusera", "testuserb"),
        ("A random private album 2", True, "testusera", "testuserb"),
        ("A random public album 3", False, "testuserb", "testusera"),
        ("A random private album 4", True, "testuserb", "testusera"),
    ),
)
def test_albums_get_private(client, session, title, private, username, username_against):
    """
    POST /api/albums/<username_or_id>/<albumslug>
    """
    # Login as user X
    client_id, client_secret, access_token = login(client, username, username)
    # Create an album
    if private:
        datas = {"title": title, "private": private}
    else:
        datas = {"title": title}
    resp = client.post("/api/albums", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert "id" in resp.json, f"{resp.status_code} - {resp.data!r}"
    assert "slug" in resp.json, f"{resp.status_code} - {resp.data!r}"
    slug = resp.json["slug"]

    # Try to fetch it with the other user
    _, _, access_token2 = login(client, username_against, username_against)
    resp = client.get(f"/api/albums/{username}/{slug}", headers=bearerhdr(access_token2))
    if private:
        assert resp.status_code == 404, f"{resp.status_code} - {resp.data!r}"
    else:
        assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
        assert resp.json["account"]["username"] == username
        assert resp.json["account"]["username"] != username_against


def test_albums_delete(client, session):
    """
    DELETE /api/albums/<username_or_id>/<albumslug>
    """

    # Login as user A
    client_id, client_secret, access_token = login(client, "testuserc", "testuserc")

    # Create an album
    datas = {"title": "testalbumtodelete"}

    resp = client.post("/api/albums", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert "id" in resp.json, f"{resp.status_code} - {resp.data!r}"
    assert "slug" in resp.json, f"{resp.status_code} - {resp.data!r}"
    slug = resp.json["slug"]

    # Get album
    resp = client.get(f"/api/albums/testuserc/{slug}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert resp.json["reel2bits"]["title"] == "testalbumtodelete"
    assert resp.json["account"]["username"] == "testuserc"

    # Delete
    resp = client.delete(f"/api/albums/testuserc/{slug}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"

    # Could not fetch it anymore
    resp = client.get(f"/api/albums/testuserc/{slug}", headers=bearerhdr(access_token))
    assert resp.status_code == 404, f"{resp.status_code} - {resp.data!r}"


def test_albums_edit(client, session):
    """
    PATCH /api/albums/<username_or_id>/<albumslug>
    """

    # Login as user C
    client_id, client_secret, access_token = login(client, "testuserc", "testuserc")

    # Create an album
    datas = {"title": "testalbumtoedit_1", "description": "desc1", "genre": "genre 1", "tags": "tag1"}

    resp = client.post("/api/albums", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert "id" in resp.json, f"{resp.status_code} - {resp.data!r}"
    assert "slug" in resp.json, f"{resp.status_code} - {resp.data!r}"
    slug = resp.json["slug"]

    # Get album
    resp = client.get(f"/api/albums/testuserc/{slug}", headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert resp.json["reel2bits"]["title"] == "testalbumtoedit_1"
    assert resp.json["reel2bits"]["genre"] == "genre 1"
    assert "tag1" in resp.json["reel2bits"]["tags"]
    assert resp.json["content"] == "desc1"
    assert resp.json["account"]["username"] == "testuserc"

    # Edit
    datas = {"title": "testalbumtoedit_2", "description": "desc2", "genre": "genre 2", "tags": ["tag2"]}
    resp = client.patch(f"/api/albums/testuserc/{slug}", json=datas, headers=headers(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    slug = resp.json["reel2bits"]["slug"]

    # Get album again
    resp = client.get(f"/api/albums/testuserc/{slug}", headers=headers(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert resp.json["reel2bits"]["title"] == "testalbumtoedit_2"
    assert resp.json["reel2bits"]["genre"] == "genre 2"
    assert "tag1" not in resp.json["reel2bits"]["tags"]
    assert "tag2" in resp.json["reel2bits"]["tags"]
    assert resp.json["content"] == "desc2"
    assert resp.json["account"]["username"] == "testuserc"


@pytest.mark.parametrize(
    ("title", "from_private", "to_private", "possible"),
    (
        ("testalbumprivacy 1", True, False, True),
        ("testalbumprivacy 2", True, True, True),
        ("testalbumprivacy 3", False, True, False),
        ("testalbumprivacy 4", False, False, True),
    ),
)
def test_albums_edit_privacy(client, session, title, from_private, to_private, possible):
    """
    PATCH /api/albums/<username_or_id>/<albumslug>
    """
    # Login as user A
    client_id, client_secret, access_token = login(client, "testuserc", "testuserc")

    # Create an album privacy X
    datas = {"title": title}
    if from_private:
        datas["private"] = True

    resp = client.post("/api/albums", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert "id" in resp.json, f"{resp.status_code} - {resp.data!r}"
    assert "slug" in resp.json, f"{resp.status_code} - {resp.data!r}"
    slug = resp.json["slug"]

    # Edit privacy to Y
    datas = {"title": title, "private": to_private, "tags": []}
    resp = client.patch(f"/api/albums/testuserc/{slug}", json=datas, headers=headers(access_token))
    if possible:
        assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
        assert resp.json["reel2bits"]["title"] == title
    else:
        assert resp.status_code == 400, f"{resp.status_code} - {resp.data!r}"
        assert "error" in resp.json


def test_albums_user_get(client, session):
    """
    GET /api/albums/<user_id>
    """

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    album1 = {"title": "testalbumuserget1", "private": False, "description": "squeak", "genre": "", "tags": ""}
    album2 = {"title": "testalbumuserget2", "private": False, "description": "squeak", "genre": "", "tags": ""}

    # Create album1
    resp = client.post("/api/albums", data=album1, headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert "id" in resp.json, f"{resp.status_code} - {resp.data!r}"
    assert "slug" in resp.json, f"{resp.status_code} - {resp.data!r}"

    # Create album2
    resp = client.post("/api/albums", data=album2, headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert "id" in resp.json, f"{resp.status_code} - {resp.data!r}"
    assert "slug" in resp.json, f"{resp.status_code} - {resp.data!r}"

    # Get user A from DB
    user = User.query.filter(User.name == "testusera").first()

    # Get user albums
    # Caveats: only short objects are implemented
    resp = client.get(f"/api/albums/{user.id}?short=true", headers=bearerhdr(access_token))
    assert resp.status_code == 200
    albumslist = [x["title"] for x in resp.json]
    assert "testalbumuserget1" in albumslist
    assert "testalbumuserget2" in albumslist
