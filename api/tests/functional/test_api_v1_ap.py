from helpers import headers
import pytest
from flask import current_app


"""
controllers/api/v1/ap.py
"""


def test_user_actor_json(client, session):
    """
    Test that we get a correct user
    /user/<name>
    """
    resp = client.get("/user/testusera", headers=headers())
    assert resp.status_code == 200
    assert resp.json["name"] == "test user a"
    assert resp.json["preferredUsername"] == "testusera"
    assert resp.json["type"] == "Person"


def test_user_actor_json_tombstone(client, session):
    """
    Test that we get a correct tombstone for deleted user
    /user/<name>
    """
    pytest.skip("matching account delete in test_accounts.py is skipped too")
    resp = client.get("/user/testuserdeleted", headers=headers())
    assert resp.status_code == 410
    print(resp.json)
    assert resp.json["type"] == "Tombstone"


def test_api_v1_instance(client, session):
    """
    /api/v1/instance
    """
    method = current_app.config["REEL2BITS_PROTOCOL"]
    domain = current_app.config["AP_DOMAIN"]

    resp = client.get("/api/v1/instance", headers=headers())
    assert resp.status_code == 200
    assert "en" in resp.json["languages"]
    assert resp.json["uri"] == f"{method}://{domain}"
