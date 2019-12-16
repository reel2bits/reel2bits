from helpers import login, logout, register, headers
from models import User

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
    assert client_id
    assert client_secret
    assert access_token

    # try to fetch own account
    resp = client.get("/api/v1/accounts/verify_credentials", headers=headers(access_token))
    assert resp.status_code == 200

    assert resp.json["display_name"] == "test user A"
    assert resp.json["username"] == "testusera"
    assert resp.json["acct"] == "testusera"

    # logout
    logged_out = logout(client)  # useless for now
    assert logged_out


def test_accounts(client, session):
    # register
    pass


def test_account_get(client, session):
    """
    Get accounts
    /api/v1/accounts/<username_or_id>
    """
    pass


def test_accounts_verify_credentials(client, session):
    """
    Test own user credentials
    /api/v1/accounts/verify_credentials
    """
    pass


def test_accounts_update_credentials(client, session):
    """
    Test updating account
    /api/v1/accounts/update_credentials
    """
    pass


def test_user_statuses(client, session):
    """
    Test getting user statuses
    /api/v1/accounts/<username_or_id>/statuses
    """
    pass


def test_relationships(client, session):
    """
    Test user relationships
    /api/v1/account/relationships
    """
    pass


def test_follow(client, session):
    """
    Test follow
    /api/v1/accounts/<username_or_id>/follow
    """
    pass


def test_unfollow(client, session):
    """
    Test unfollow
    /api/v1/accounts/<username_or_id>/unfollow
    """
    pass


def test_followers(client, session):
    """
    Test followers list
    /api/v1/accounts/<username_or_id>/followers
    """
    pass


def test_followings(client, session):
    """
    Test followings list
    /api/v1/accounts/<username_or_id>/followings
    """
    pass


def test_account_delete(client, session):
    """
    Test delete account
    /api/v1/accounts
    """
    pass
