from helpers import register, assert_valid_schema
from flask import current_app
import json


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


def test_nodeinfo_2_0(client, session):
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

    # Test nodeinfo returned json (2.0)
    rv = client.get("/nodeinfo/2.0")
    assert (
        rv.headers["Content-Type"] == "application/json; "
        "charset=utf-8; profile="
        '"http://nodeinfo.diaspora.'
        'software/ns/schema/2.0#"'
    )
    assert rv.status_code == 200

    assert_valid_schema(rv.json, "nodeinfo-2.0.json")


def test_nodeinfo_2_1(client, session):
    # Test well-known discovery
    rv = client.get("/.well-known/nodeinfo")
    assert rv.headers["Content-Type"] == "application/json; charset=utf-8"
    assert rv.status_code == 200

    datas = rv.json
    assert "links" in datas
    node = {
        "href": f"https://{current_app.config['AP_DOMAIN']}/nodeinfo/2.1",
        "rel": "http://nodeinfo.diaspora.software/ns/schema/2.1",
    }
    assert node in datas["links"]

    # Test nodeinfo returned json (2.1)
    rv = client.get("/nodeinfo/2.1")
    assert (
        rv.headers["Content-Type"] == "application/json; "
        "charset=utf-8; profile="
        '"http://nodeinfo.diaspora.'
        'software/ns/schema/2.1#"'
    )
    assert rv.status_code == 200

    assert_valid_schema(rv.json, "nodeinfo-2.1.json")
