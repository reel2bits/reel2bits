from helpers import headers, login
import pytest


"""
controllers/api/account.py
"""


def test_logs(client, session):
    """
    GET /api/users/<username>/logs
    """
    pytest.skip("deal with it later")
    # login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    resp = client.get("/api/users/testusera/logs", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)
    items = resp.json.get("totalItems")
    assert isinstance(items, list)


def test_quota(client, session):
    """
    GET /api/users/<username>/quota
    """
    pytest.skip("deal with it later")
    # login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    resp = client.get("/api/users/testusera/quota", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)
    items = resp.json.get("totalItems")
    assert isinstance(items, list)
