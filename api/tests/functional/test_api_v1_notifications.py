from helpers import headers, login


"""
controllers/api/v1/notifications.py
"""


def test_notifications(client, session):
    """
    /api/v1/notifications
    """
    # login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # then fetch notifications
    resp = client.get("/api/v1/notifications", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, list)
