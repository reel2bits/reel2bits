import pytest

"""
controllers/api/embed.py
"""


@pytest.mark.parametrize(("kind"), (("user"), ("track"), ("album")))
def test_iframe_get(client, session, kind):
    """
    GET /api/embed/<kind>/<id>
    Caveats: Actually not implemented, it returns ""
    TODO when implemented: create a track, check exists, and get iframe
    """
    resp = client.get(f"/api/embed/{kind}/42")
    assert resp.status_code == 200
    assert resp.data == b""


def test_iframe_invalid_kind_get(client, session):
    """
    GET /api/embed/<kind>/<id>
    """
    resp = client.get("/api/embed/uwu/42")
    assert resp.status_code == 400
