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


def test_config_kernel_manager(voila_app):
    assert voila_app.serverapp.kernel_manager.cull_interval == 10


def test_config_contents_manager(voila_app):
    assert voila_app.serverapp.contents_manager.use_atomic_writing is False


async def test_template(fetch):
    response = await fetch('voila', method='GET')
    assert response.code == 200
    assert 'test_template.css' in response.body.decode('utf-8')
    assert 'Hi Voila' in response.body.decode('utf-8')
