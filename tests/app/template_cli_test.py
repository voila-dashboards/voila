# tests programmatic config of template sytem
import pytest
import os

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_args_extra():
    path_gridstack = os.path.abspath(os.path.join(BASE_DIR, '../../share/jupyter/voila/templates/gridstack/nbconvert_templates'))
    path_default = os.path.abspath(os.path.join(BASE_DIR, '../../share/jupyter/voila/templates/default/nbconvert_templates'))
    return ['--template=None', '--Voila.nbconvert_template_paths=[%r, %r]' % (path_gridstack, path_default)] 


@pytest.mark.gen_test
def test_template_gridstack(http_client, base_url):
    response = yield http_client.fetch(base_url)
    assert response.code == 200
    assert 'gridstack.css' in response.body.decode('utf-8')
    assert 'Hi Voila' in response.body.decode('utf-8')
