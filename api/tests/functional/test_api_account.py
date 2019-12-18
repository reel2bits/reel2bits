from helpers import headers, login


"""
controllers/api/account.py
"""


def test_logs(client, session):
    """
    GET /api/users/<username>/logs
    """
    # login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    resp = client.get("/api/users/testusera/logs", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)
    items = resp.json.get("items")
    assert isinstance(items, list)


# TODO add a track to test logs content


def test_quota(client, session):
    """
    GET /api/users/<username>/quota
    """
    # login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    resp = client.get("/api/users/testusera/quota", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)
    items = resp.json.get("items")
    assert isinstance(items, list)


# TODO add a track to test quota change
