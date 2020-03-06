# tests programmatic config of template sytem
import pytest

import os

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_args_extra():
    return ['--template=None']


@pytest.fixture
def voila_config():
    path_test_template = os.path.abspath(os.path.join(BASE_DIR, '../test_template/share/jupyter/voila/templates/test_template/nbconvert_templates'))
    path_default = os.path.abspath(os.path.join(BASE_DIR, '../../share/jupyter/voila/templates/default/nbconvert_templates'))
    path = os.path.abspath(os.path.join(BASE_DIR, '../../share/jupyter/voila/templates/default/templates'))
    config = dict(
        nbconvert_template_paths=[path_test_template, path_default],
        template_paths=[path]
    )
    return config


async def test_template(fetch, token):
    response = await fetch('voila', params={'token': token}, method='GET')
    assert response.code == 200
    assert 'test_template.css' in response.body.decode('utf-8')
    assert 'Hi Voila' in response.body.decode('utf-8')
