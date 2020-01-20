from helpers import headers, bearerhdr, login


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


def test_logs_new_album(client, session):
    """
    POST /api/albums
    """

    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    datas = {"title": "some album log", "description": "squeak", "genre": "none", "tags": "meow"}

    resp = client.post("/api/albums", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert "id" in resp.json, f"{resp.status_code} - {resp.data!r}"
    assert "slug" in resp.json, f"{resp.status_code} - {resp.data!r}"

    # Get logs
    resp = client.get("/api/users/testusera/logs", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)
    items = resp.json.get("items")
    assert isinstance(items, list)
    count = len(items)

    # Add another album
    datas = {"title": "some album log 2", "description": "squeak squeak", "genre": "none", "tags": "meow"}
    resp = client.post("/api/albums", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 200, f"{resp.status_code} - {resp.data!r}"
    assert "id" in resp.json, f"{resp.status_code} - {resp.data!r}"
    assert "slug" in resp.json, f"{resp.status_code} - {resp.data!r}"

    # Get logs
    resp = client.get("/api/users/testusera/logs", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)
    items = resp.json.get("items")
    assert isinstance(items, list)

    assert len(items) > count


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
