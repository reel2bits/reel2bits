from helpers import register
from flask import current_app
import json

"""
controllers/api/v1/well_known.py
"""


def test_host_meta(client, session):
    method = current_app.config["REEL2BITS_PROTOCOL"]
    domain = current_app.config["AP_DOMAIN"]
    resp = client.get("/.well-known/host-meta")
    assert resp.status_code
    assert f"{method}://{domain}/.well-known/webfinger?resource={{uri}}".encode() in resp.data


def test_webfinger(client, session):
    resp = register(client, "dashie+webfinger@sigpipe.me", "fluttershy", "TestWebfinger", "Test Webfinger")
    assert resp.status_code == 200

    resp = json.loads(resp.data)
    assert "created_at" in resp
    assert "access_token" in resp

    rv = client.get(f"/.well-known/webfinger?resource=acct:TestWebfinger@{current_app.config['AP_DOMAIN']}")
    assert rv.status_code == 200

    assert rv.headers["Content-Type"] == "application/jrd+json; charset=utf-8"

    datas = rv.json

    assert "aliases" in datas
    assert f"https://{current_app.config['AP_DOMAIN']}/user/TestWebfinger" in datas["aliases"]
    assert "links" in datas
    assert "subject" in datas
    assert datas["subject"] == f"acct:TestWebfinger@" f"{current_app.config['AP_DOMAIN']}"


def test_webfinger_case(client, session):
    resp = register(client, "dashie+webfingercase@sigpipe.me", "fluttershy", "TestWebfingerCase", "Test Webfinger Case")
    assert resp.status_code == 200

    resp = json.loads(resp.data)
    assert "created_at" in resp
    assert "access_token" in resp

    rv = client.get(f"/.well-known/webfinger?resource=acct:testwebfingercase@{current_app.config['AP_DOMAIN']}")
    assert rv.status_code == 200

    assert rv.headers["Content-Type"] == "application/jrd+json; charset=utf-8"

    datas = rv.json

    assert "aliases" in datas
    assert f"https://{current_app.config['AP_DOMAIN']}" f"/user/TestWebfingerCase" in datas["aliases"]
    assert "links" in datas
    assert "subject" in datas
    assert datas["subject"] == f"acct:TestWebfingerCase@" f"{current_app.config['AP_DOMAIN']}"


def test_unknown_webfinger(client, session):
    rv = client.get(f"/.well-known/webfinger?resource=acct:TestWebfinger83294289@{current_app.config['AP_DOMAIN']}")
    assert rv.headers["Content-Type"] == "application/jrd+json; charset=utf-8"
    assert rv.status_code == 404


def test_nodeinfo(client, session):
    # Test well-known discovery
    rv = client.get("/.well-known/nodeinfo")
    assert rv.headers["Content-Type"] == "application/json; charset=utf-8"
    assert rv.status_code == 200

    datas = rv.json
    assert "links" in datas
    node = {
        "href": f"https://{current_app.config['AP_DOMAIN']}/nodeinfo/2.0",
        "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
    }
    assert node in datas["links"]
