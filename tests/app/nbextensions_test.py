# tests programmatic config of template sytem
import pytest
import os

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_config():
    os.environ['JUPYTER_CONFIG_DIR'] = os.path.join(BASE_DIR, '../configs/general')
    yield {}
    del os.environ['JUPYTER_CONFIG_DIR']


@pytest.fixture
def voila_config_file_paths_arg():
    # we don't want the tests to use any configuration on the system
    path = os.path.abspath(os.path.join(BASE_DIR, '../configs/general'))
    return '--Voila.config_file_paths=[%r]' % path


async def test_lists_extension(fetch, token):
    response = await fetch('voila', params={'token': token}, method='GET')
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voila' in html_text
    assert 'ipytest/extension.js' in html_text
