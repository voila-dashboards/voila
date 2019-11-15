# tests programmatic config of template sytem
import pytest

import os

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_config():
    def config(app):
        pass
    os.environ['JUPYTER_CONFIG_DIR'] = os.path.join(BASE_DIR, '../configs/general')
    yield config
    del os.environ['JUPYTER_CONFIG_DIR']


@pytest.fixture
def voila_config_file_paths_arg():
    # we don't want the tests to use any configuration on the system
    path = os.path.abspath(os.path.join(BASE_DIR, '../configs/general'))
    return '--VoilaTest.config_file_paths=[%r]' % path


@pytest.mark.gen_test
def test_lists_extension(http_client, base_url):
    response = yield http_client.fetch(base_url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voila' in html_text
    assert 'ipytest/extension.js' in html_text
