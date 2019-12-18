from helpers import headers, login
from models import User


"""
controllers/api/v1/timelines.py
"""

# Long-term TODO: populate enough stuff to properly test pagination


def test_home(client, session):
    """
    /api/v1/timelines/home
    """
    # login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # then fetch timeline
    resp = client.get("/api/v1/timelines/home", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)


def test_public_paginated(client, session):
    """
    /api/v1/timelines/public
    """
    # fetch timeline
    resp = client.get("/api/v1/timelines/public?paginated=true", headers=headers())
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)


def test_public_mastoapi(client, session):
    """
    /api/v1/timelines/public
    """
    # fetch timeline
    resp = client.get("/api/v1/timelines/public", headers=headers())
    assert resp.status_code == 200
    assert isinstance(resp.json, list)


def test_drafts(client, session):
    """
    /api/v1/timelines/drafts
    """
    # login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # fetch timeline
    resp = client.get("/api/v1/timelines/drafts", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)


def test_albums(client, session):
    """
    /api/v1/timelines/albums
    """
    # get user and flake_id
    user = User.query.filter(User.name == "testusera").first()
    # fetch timeline
    resp = client.get(f"/api/v1/timelines/albums?user={user.flake_id}", headers=headers())
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)


def test_unprocessed(client, session):
    """
    /api/v1/timelines/unprocessed
    """
    # login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # fetch timeline
    resp = client.get("/api/v1/timelines/unprocessed", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)
