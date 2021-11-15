# tests programmatic config of template system
import pytest

import os

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def jupyter_server_config():
    def config(app):
        pass
    os.environ['JUPYTER_CONFIG_DIR'] = os.path.join(BASE_DIR, '..', 'configs', 'general')
    yield config
    del os.environ['JUPYTER_CONFIG_DIR']


@pytest.mark.xfail(reason='needs to be fixed')
async def test_lists_extension(http_server_client, print_notebook_url):
    response = await http_server_client.fetch(print_notebook_url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voilà' in html_text
    assert 'ipytest/extension.js' in html_text
