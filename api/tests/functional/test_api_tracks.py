from helpers import login, bearerhdr
from werkzeug.datastructures import FileStorage

"""
controllers/api/tracks.py
"""

"""
# TODO
GET /api/tracks/<username_or_id>/<soundslug>

DELETE /api/tracks/<username>/<soundslug>

PATCH /api/tracks/<username>/<soundslug>

GET /api/tracks/<username_or_id>/<soundslug>

POST /api/tracks/<username_or_id>/<soundslug>/retry_processing

PATCH /api/tracks/<username>/<soundslug>/artwork
"""


def test_track_upload(client, session):
    """
    POST /api/tracks
    """
    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {
        "title": "test track upload",
        "licence": 0,  # unspecified, see api/utils/defaults.py
        "description": "test track upload",
        "private": False,
        "file": FileStorage(stream=open("tests/assets/cat.mp3", "rb"), filename="cat.mp3"),
    }
    resp = client.post("/api/tracks", data=datas, headers=bearerhdr(access_token), content_type="multipart/form-data")
    assert resp.status_code == 200, resp.data
    assert len(resp.json["id"]) == 36
    assert len(resp.json["slug"]) >= 5


# TODO: Create {tags, private true, artwork, missing fields, title define/undefine}
# Title (no: filename)
# description w/ & w/out
# album
# private true/false
# tags & w/out tags
# transcoding
