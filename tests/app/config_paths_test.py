# test all objects that should be configurable
import pytest

import os


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_config_file_paths_arg():
    path = os.path.join(BASE_DIR, '..', 'configs', 'general')
    return '--VoilaTest.config_file_paths=[%r]' % path


def test_config_app(voila_app):
    assert voila_app.voila_configuration.template == 'test_template'


def test_config_kernel_manager(voila_app):
    assert voila_app.kernel_manager.cull_interval == 10


def test_config_contents_manager(voila_app):
    assert voila_app.contents_manager.use_atomic_writing is False


async def test_template(http_server_client, base_url):

    response = await http_server_client.fetch(base_url)
    assert response.code == 200
    assert 'test_template.css' in response.body.decode('utf-8')
    assert 'Hi Voilà' in response.body.decode('utf-8')
