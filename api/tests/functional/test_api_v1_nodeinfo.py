from helpers import assert_valid_schema
from flask import current_app

"""
controllers/api/v1/nodeinfo.py
"""


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

    # this is ugly but we need to patch this because we disable outside AP broadcasts in tests
    rv.json["protocols"] = ["activitypub"]

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

    # this is ugly but we need to patch this because we disable outside AP broadcasts in tests
    rv.json["protocols"] = ["activitypub"]

    assert_valid_schema(rv.json, "nodeinfo-2.1.json")
