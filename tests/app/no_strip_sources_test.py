import pytest

import os


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_args_extra():
    return ['--VoilaConfiguration.strip_sources=False', '--VoilaExecutor.timeout=240']


async def test_no_strip_sources(http_server_client, jp_base_url):
    response = await http_server_client.fetch(jp_base_url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voilà' in html_text
    assert 'print' in html_text, 'the source code should *NOT* be stripped'
