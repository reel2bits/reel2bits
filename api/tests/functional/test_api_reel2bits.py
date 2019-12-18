from helpers import headers

"""
controllers/api/reel2bits.py
"""


def test_licenses(client, session):
    """
    GET /api/reel2bits/licenses
    """
    resp = client.get("/api/reel2bits/licenses", headers=headers())
    assert resp.status_code == 200
    assert isinstance(resp.json, list)
    assert len(resp.json) > 4


def test_genres(client, session):
    """
    GET /api/reel2bits/genres
    """
    resp = client.get("/api/reel2bits/genres", headers=headers())
    assert resp.status_code == 200
    assert isinstance(resp.json, list)


# TODO genres filtering query


def test_tags(client, session):
    """
    GET /api/reel2bits/tags
    """
    resp = client.get("/api/reel2bits/tags", headers=headers())
    assert resp.status_code == 200
    assert isinstance(resp.json, list)


# TODO tags filtering query

# TODO POST /api/reel2bits/change_password
