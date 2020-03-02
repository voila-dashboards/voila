import pytest

import os


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_args_extra():
    return ['--Voila.strip_sources=False']


async def test_no_strip_sources(http_client, default_url):
    response = yield http_client.fetch(default_url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voila' in html_text
    assert 'print' in html_text, 'the source code should *NOT* be stripped'
