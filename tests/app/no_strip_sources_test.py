import pytest

import os


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_args_extra():
    return ['--Voila.strip_sources=False']


async def test_no_strip_sources(fetch, token):
    response = await fetch('voila', params={'token': token}, method='GET')
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voila' in html_text
    assert 'print' in html_text, 'the source code should *NOT* be stripped'
