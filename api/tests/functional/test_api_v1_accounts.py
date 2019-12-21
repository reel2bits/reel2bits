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
    resp = register(client, "testuserll@reel2bits.org", "testuserll", "testuserll", "test user ll")
    assert resp.status_code == 200

    user = User.query.filter(User.name == "testuserll").first()
    assert user.check_password("testuserll")
    assert user.local
    assert user.confirmed_at
    assert user.active

    # try to login
    client_id, client_secret, access_token = login(client, "testuserll", "testuserll")

    # try to fetch own account
    resp = client.get("/api/v1/accounts/verify_credentials", headers=headers(access_token))
    assert resp.status_code == 200

    assert resp.json["display_name"] == "test user ll"
    assert resp.json["username"] == "testuserll"
    assert resp.json["acct"] == "testuserll"

    # logout
    logged_out = logout(client)  # useless for now
    assert logged_out


def test_invalid_login(client, session):
    """
    Makes sure an invalid login don't work
    """
    client_id, client_secret, access_token = login(client, "idontexist", "atall", should_fail=True)
    assert not client_id
    assert not client_secret
    assert not access_token


def test_register_another_user(client, session):
    """
    Register an user ll
    """
    resp = register(client, "testuserll2@reel2bits.org", "testuserll2", "testuserll2", "test user ll2")
    assert resp.status_code == 200

    user = User.query.filter(User.name == "testuserll2").first()
    assert user.check_password("testuserll2")
    assert user.local
    assert user.confirmed_at
    assert user.active


@pytest.mark.parametrize(
    ("email", "password", "username", "display_name"),
    (
        ("invalidemail", "aaaaa", "coin", "pouet pouet"),
        ("okemail@reel2bits.org", "some password", "invalid username", "display name"),
        ("okemail@reel2bits.org", "", "username", "aaa"),
        ("", "aaaaa", "aaaa", "aaaa"),
        ("okemail@reel2bits.org", "aaaaa", "", "oh"),
        ("testusera@reel2bits.org", "aaaaa", "aaa", "aaa"),
        ("okemail@reel2bits.org", "aaaaaa", "testusera", "testuseraaa"),
    ),
)
def test_register_invalid(client, session, email, password, username, display_name):
    """
    Test registering invalid users
    """
    resp = register(client, email, password, username, display_name, should_fail=True)
    assert resp.status_code == 400


def test_account_get_with_bearer(client, session):
    """
    Get accounts
    /api/v1/accounts/<username_or_id>
    """
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    resp = client.get("/api/v1/accounts/testusera", headers=headers(access_token))
    assert resp.status_code == 200

    assert resp.json["display_name"] == "test user a"
    assert resp.json["username"] == "testusera"
    assert resp.json["acct"] == "testusera"


def test_account_get_with_wrong_bearer(client, session):
    """
    Get accounts
    /api/v1/accounts/<username_or_id>
    """
    resp = client.get("/api/v1/accounts/testusera", headers=headers("ottersdoessqueaksqueak"))
    assert resp.status_code == 401


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
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

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


def test_follow_insexistant_user(client, session):
    """
    Test follow with inexistant user
    /api/v1/accounts/<username_or_id>/follow

    user A follow inexistant user
    """
    # Login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # then follow user DAVENULL
    resp = client.post("/api/v1/accounts/davenull/follow", headers=headers(access_token))
    assert resp.status_code == 404


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


def test_unfollow_inexistant_user(client, session):
    """
    Test unfollow inexistant user
    /api/v1/accounts/<username_or_id>/unfollow
    """
    # login as user A
    client_id, client_secret, access_token = login(client, "testusera", "testusera")

    # then unfollow user DAVENULL
    resp = client.post("/api/v1/accounts/davenull/unfollow", headers=headers(access_token))
    assert resp.status_code == 404


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
