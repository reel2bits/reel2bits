from helpers import assert_valid_schema
import pytest

"""
controllers/api/v1/nodeinfo.py
"""


@pytest.mark.parametrize(("version"), (("2.0"), ("2.1")))
def test_nodeinfo(client, session, version):
    # Test nodeinfo returned json (x.y)
    rv = client.get(f"/nodeinfo/{version}")
    _str = f'application/json; charset=utf-8; profile="http://nodeinfo.diaspora.software/ns/schema/{version}#"'
    assert rv.headers["Content-Type"] == _str
    assert rv.status_code == 200

    # this is ugly but we need to patch this because we disable outside AP broadcasts in tests
    rv.json["protocols"] = ["activitypub"]

    assert_valid_schema(rv.json, f"nodeinfo-{version}.json")
