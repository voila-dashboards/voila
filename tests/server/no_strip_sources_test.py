import pytest

import os


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def jupyter_server_args_extra():
    return ['--VoilaConfiguration.strip_sources=False']


async def test_hello_world(http_server_client, print_notebook_url):
    response = await http_server_client.fetch(print_notebook_url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voila' in html_text
    assert 'print' in html_text, 'the source code should *NOT* be stripped'
