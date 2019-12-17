from helpers import login, logout, register, headers
from models import User
import json
import pytest

"""
controllers/api/v1/accounts.py
"""


def test_login_logout(client, session):
    """
    Make sure login and logout works
    """
    resp = register(client, "testusera@reel2bits.org", "testusera", "testusera", "test user A")
    assert resp.status_code == 200

    user = User.query.filter(User.name == "testusera").first()
    assert user.check_password("testusera")
    assert user.local
    assert user.confirmed_at
    assert user.active

    # try to login
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # try to fetch own account
    resp = client.get("/api/v1/accounts/verify_credentials", headers=headers(access_token))
    assert resp.status_code == 200

    assert resp.json["display_name"] == "test user A"
    assert resp.json["username"] == "testusera"
    assert resp.json["acct"] == "testusera"

    # logout
    logged_out = logout(client)  # useless for now
    assert logged_out


def test_register_another_user(client, session):
    """
    Register an user B
    """
    resp = register(client, "testuserb@reel2bits.org", "testuserb", "testuserb", "test user B")
    assert resp.status_code == 200

    user = User.query.filter(User.name == "testuserb").first()
    assert user.check_password("testuserb")
    assert user.local
    assert user.confirmed_at
    assert user.active


def test_account_get_with_bearer(client, session):
    """
    Get accounts
    /api/v1/accounts/<username_or_id>
    """
    client_id, client_secret, access_token = login(client, "testuserb", "testuserb")

    resp = client.get("/api/v1/accounts/testusera", headers=headers(access_token))
    assert resp.status_code == 200

    assert resp.json["display_name"] == "test user A"
    assert resp.json["username"] == "testusera"
    assert resp.json["acct"] == "testusera"


def test_account_update_credentials_change_bio(client, session):
    """
    Test updating account (change bio)
    /api/v1/accounts/update_credentials
    """
    # check bio is empty
    resp = client.get("/api/v1/accounts/testusera", headers=headers())
    assert resp.status_code == 200
    assert not resp.json["note"]

    # login
    client_id, client_secret, access_token = login(client, "testuserb", "testuserb")

    # update and check return
    resp = client.patch(
        "/api/v1/accounts/update_credentials", data=json.dumps({"bio": "squeak squeak"}), headers=headers(access_token)
    )
    assert resp.status_code == 200
    assert resp.json["note"] == "squeak squeak"


def test_user_statuses_empty(client, session):
    """
    Test getting user statuses
    /api/v1/accounts/<username_or_id>/statuses
    """
    resp = client.get("/api/v1/accounts/testusera/statuses", headers=headers())
    assert resp.status_code == 200
    assert resp.json["page"] == 1
    assert resp.json["totalItems"] == 0


def test_relationships_empty(client, session):
    """
    Test user relationships (empty set)
    /api/v1/account/relationships
    """
    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # Get relationships, should be empty
    resp = client.get(f"/api/v1/accounts/relationships/", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, list)
    assert len(resp.json) == 0


def test_follow(client, session):
    """
    Test follow
    /api/v1/accounts/<username_or_id>/follow

    user A follow user B
    """
    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # then follow user B
    resp = client.post("/api/v1/accounts/testuserb/follow", headers=headers(access_token))
    assert resp.status_code in [200, 202]  # local, remote

    # get userb flake_id
    userB = User.query.filter(User.name == "testuserb").first()
    assert userB.flake_id
    # get relationship between A and B
    resp = client.get(f"/api/v1/accounts/relationships/?id={userB.flake_id}", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, list)
    rel = resp.json[0]
    assert rel["id"] != userB.flake_id
    assert rel["following"] is True
    assert rel["followed_by"] is False  # not yet followed
    assert rel["blocking"] is False
    assert rel["muting"] is False


def test_followers(client, session):
    """
    Test followers list
    /api/v1/accounts/<username_or_id>/followers
    """
    # A follow B, A has no followers, B has one follower
    # get followers for user A
    resp = client.get("/api/v1/accounts/testusera/followers", headers=headers())
    assert resp.status_code == 200
    assert resp.json["page"] == 1
    assert resp.json["totalItems"] == 0
    assert len(resp.json["items"]) == 0

    # get followers for user B
    resp = client.get("/api/v1/accounts/testuserb/followers", headers=headers())
    assert resp.status_code == 200
    assert resp.json["page"] == 1
    assert resp.json["totalItems"] == 1
    assert len(resp.json["items"]) == 1


def test_followings(client, session):
    """
    Test followings list
    /api/v1/accounts/<username_or_id>/following
    """
    # A follow B, A has one following, B has no followings
    # get followers for user A
    resp = client.get("/api/v1/accounts/testusera/following", headers=headers())
    assert resp.status_code == 200
    assert resp.json["page"] == 1
    assert resp.json["totalItems"] == 1
    assert len(resp.json["items"]) == 1

    # get followers for user B
    resp = client.get("/api/v1/accounts/testuserb/following", headers=headers())
    assert resp.status_code == 200
    assert resp.json["page"] == 1
    assert resp.json["totalItems"] == 0
    assert len(resp.json["items"]) == 0


def test_unfollow(client, session):
    """
    Test unfollow
    /api/v1/accounts/<username_or_id>/unfollow
    """
    # login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # then unfollow user B
    resp = client.post("/api/v1/accounts/testuserb/unfollow", headers=headers(access_token))
    assert resp.status_code in [200, 202]  # local and remote

    # check relationship
    # get userb flake_id
    userB = User.query.filter(User.name == "testuserb").first()
    assert userB.flake_id
    # get relationship between A and B
    resp = client.get(f"/api/v1/accounts/relationships/?id={userB.flake_id}", headers=headers(access_token))
    assert resp.status_code == 200
    assert isinstance(resp.json, list)
    rel = resp.json[0]
    assert rel["id"] != userB.flake_id
    assert rel["following"] is False
    assert rel["followed_by"] is False
    assert rel["blocking"] is False
    assert rel["muting"] is False


def test_account_delete(client, session):
    """
    Test delete account
    /api/v1/accounts
    """
    pytest.skip("doesn't make sqlalchemy happy")
    # register a new user
    resp = register(client, "testuserdeleted@reel2bits.org", "testuserdeleted", "testuserdeleted", "test user deleted")
    assert resp.status_code == 200

    # user exists
    resp = client.get("/api/v1/accounts/testuserdeleted", headers=headers())
    assert resp.status_code == 200
    assert resp.json["display_name"] == "test user deleted"
    assert resp.json["username"] == "testuserdeleted"
    assert resp.json["acct"] == "testuserdeleted"

    # login and delete account
    client_id, client_secret, access_token = login(client, "testuserdeleted", "testuserdeleted")

    resp = client.delete("/api/v1/accounts", headers=headers(access_token))
    assert resp.status_code == 200

    # try to fetch deleted account
    resp = client.get("/api/v1/accounts/testuserdeleted", headers=headers())
    assert resp.status_code == 404