from tests.helpers import logout, register, assert_valid_schema
from flask import current_app


def test_webfinger(client, session):
    register(client,
             "dashie+webfinger@sigpipe.me",
             "fluttershy",
             "TestWebfinger")
    logout(client)

    rv = client.get(
        '/.well-known/webfinger?resource=acct:TestWebfinger@localhost')
    assert rv.status_code == 200

    assert rv.headers['Content-Type'] == 'application/jrd+json; charset=utf-8'

    datas = rv.json

    assert 'aliases' in datas
    assert f"https://{current_app.config['AP_DOMAIN']}/user/TestWebfinger" in \
           datas['aliases']
    assert 'links' in datas
    assert 'subject' in datas
    assert datas['subject'] == f"acct:TestWebfinger@" \
                               f"{current_app.config['AP_DOMAIN']}"


def test_webfinger_case(client, session):
    register(client,
             "dashie+webfingercase@sigpipe.me",
             "fluttershy",
             "TestWebfingerCase")
    logout(client)

    rv = client.get(
        '/.well-known/webfinger?resource=acct:testwebfingercase@localhost')
    assert rv.status_code == 200

    assert rv.headers['Content-Type'] == 'application/jrd+json; charset=utf-8'

    datas = rv.json

    assert 'aliases' in datas
    assert f"https://{current_app.config['AP_DOMAIN']}" \
           f"/user/TestWebfingerCase" in datas['aliases']
    assert 'links' in datas
    assert 'subject' in datas
    assert datas['subject'] == f"acct:TestWebfingerCase@" \
                               f"{current_app.config['AP_DOMAIN']}"


def test_unknown_webfinger(client, session):
    rv = client.get(
        '/.well-known/webfinger?resource=acct:TestWebfinger83294289@localhost')
    assert rv.headers['Content-Type'] == 'application/jrd+json; charset=utf-8'
    assert rv.status_code == 404


def test_nodeinfo(client, session):
    # Test well-known discovery
    rv = client.get('/.well-known/nodeinfo')
    assert rv.headers['Content-Type'] == 'application/json; charset=utf-8'
    assert rv.status_code == 200

    datas = rv.json
    assert 'links' in datas
    node = {
        "href": f"https://{current_app.config['AP_DOMAIN']}/nodeinfo/2.0",
        "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0"
    }
    assert node in datas['links']

    # Test nodeinfo returned json (2.0)
    rv = client.get('/nodeinfo/2.0')
    assert rv.headers['Content-Type'] == \
           'application/json; charset=utf-8; ' \
           'profile="http://nodeinfo.diaspora.software/ns/schema/2.0#"'
    assert rv.status_code == 200

    assert_valid_schema(rv.json, "nodeinfo-2.0.json")
