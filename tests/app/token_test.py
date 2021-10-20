# test all objects that should be configurable
import pytest
import tornado

import os

from secrets import token_hex

BASE_DIR = os.path.dirname(__file__)
TOKEN = token_hex()


@pytest.fixture
def base_url():
    return "/?token=%s" % TOKEN


@pytest.fixture
def voila_args_extra():
    return ['--VoilaTest.token=%s' % TOKEN, '--VoilaExecutor.timeout=240']


async def test_token(http_server_client, base_url):

    response = await http_server_client.fetch(base_url)
    assert response.code == 200
    assert 'Hi Voilà' in response.body.decode('utf-8')


async def test_missing_token(http_server_client):

    with pytest.raises(tornado.httpclient.HTTPClientError, match='HTTP 404.*'):
        await http_server_client.fetch('/')


async def test_wrong_token(http_server_client):

    with pytest.raises(tornado.httpclient.HTTPClientError, match='HTTP 404.*'):
        await http_server_client.fetch("/?token=%s" % token_hex())
