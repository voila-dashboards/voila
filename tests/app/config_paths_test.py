# test all objects that should be configurable
import pytest
import os


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_config_file_paths_arg():
    path = os.path.join(BASE_DIR, '..', 'configs', 'general')
    return '--Voila.config_file_paths=[%r]' % path


def test_config_app(voila_app):
    assert voila_app.template == 'test_template'
    assert voila_app.enable_nbextensions is True


async def test_template(http_client, default_url):
    response = yield http_client.fetch(default_url)
    assert response.code == 200
    assert 'test_template.css' in response.body.decode('utf-8')
    assert 'Hi Voila' in response.body.decode('utf-8')
