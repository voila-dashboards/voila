# tests config of template sytem from JSON file
import pytest

import os

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_args_extra():
    path_test_template = os.path.abspath(os.path.join(BASE_DIR, '../test_template/share/jupyter/voila/templates'))
    path_default = os.path.abspath(os.path.join(BASE_DIR, '../../share/jupyter/voila/templates/default/nbconvert_templates'))
    path_config = os.path.abspath(os.path.join(BASE_DIR, '../test_template/share/jupyter/voila/templates/test_template/conf.json'))
    return ['--Voila.template=test_template', '--Voila.nbconvert_template_paths=[%r, %r]' % (path_test_template, path_default), '--ServerApp.config_file=%r' % path_config]


async def test_template_test(fetch, token):
    response = await fetch('voila', params={'token': token}, method='GET')
    assert response.code == 200
    assert 'test_template.css' in response.body.decode('utf-8')
    assert 'Hi Voila' in response.body.decode('utf-8')
    assert 'test resource from config file' in response.body.decode('utf-8')
