from helpers import register
from flask import current_app
import json
import pytest

"""
controllers/api/v1/well_known.py
"""


def test_host_meta(client, session):
    method = current_app.config["REEL2BITS_PROTOCOL"]
    domain = current_app.config["AP_DOMAIN"]
    resp = client.get("/.well-known/host-meta")
    assert resp.status_code
    assert f"{method}://{domain}/.well-known/webfinger?resource={{uri}}".encode() in resp.data


@pytest.mark.parametrize(
    ("email", "password", "username", "display_name"),
    (
        ("dashie+webfinger@reel2bits.org", "fluttershy", "TestWebfinger", "Test Webfinger"),
        ("dashie+webfingercase@reel2bits.org", "fluttershy", "TestWebfingerCase", "Test Webfinger Case"),
    ),
)
def test_webfinger(client, session, email, password, username, display_name):
    resp = register(client, email, password, username, display_name)
    assert resp.status_code == 200

    resp = json.loads(resp.data)
    assert "created_at" in resp
    assert "access_token" in resp

    rv = client.get(f"/.well-known/webfinger?resource=acct:{username}@{current_app.config['AP_DOMAIN']}")
    assert rv.status_code == 200

    assert rv.headers["Content-Type"] == "application/jrd+json; charset=utf-8"

    datas = rv.json

    assert "aliases" in datas
    assert f"https://{current_app.config['AP_DOMAIN']}/user/{username}" in datas["aliases"]
    assert "links" in datas
    assert "subject" in datas
    assert datas["subject"] == f"acct:{username}@" f"{current_app.config['AP_DOMAIN']}"


def test_unknown_webfinger(client, session):
    rv = client.get(f"/.well-known/webfinger?resource=acct:TestWebfinger83294289@{current_app.config['AP_DOMAIN']}")
    assert rv.headers["Content-Type"] == "application/jrd+json; charset=utf-8"
    assert rv.status_code == 404


@pytest.mark.parametrize(("version"), (("2.0"), ("2.1")))
def test_nodeinfo(client, session, version):
    # Test well-known discovery
    rv = client.get("/.well-known/nodeinfo")
    assert rv.headers["Content-Type"] == "application/json; charset=utf-8"
    assert rv.status_code == 200

    datas = rv.json
    assert "links" in datas
    node = {
        "href": f"https://{current_app.config['AP_DOMAIN']}/nodeinfo/{version}",
        "rel": f"http://nodeinfo.diaspora.software/ns/schema/{version}",
    }
    assert node in datas["links"]
