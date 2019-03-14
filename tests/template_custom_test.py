# tests programmatic config of template sytem
import pytest
import os

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_args_extra():
    return ['--template=None']


@pytest.fixture
def voila_config():
    def config(app):
        path_gridstack = os.path.abspath(os.path.join(BASE_DIR, '../share/jupyter/voila/template/gridstack/nbconvert_templates'))
        path_default = os.path.abspath(os.path.join(BASE_DIR, '../share/jupyter/voila/template/default/nbconvert_templates'))
        app.nbconvert_template_paths = [path_gridstack, path_default]
        path = os.path.abspath(os.path.join(BASE_DIR, '../share/jupyter/voila/template/default/templates'))
        app.template_paths = [path]

    return config


@pytest.mark.gen_test
def test_template_gridstack(http_client, base_url):
    response = yield http_client.fetch(base_url)
    assert response.code == 200
    assert 'gridstack.css' in response.body.decode('utf-8')
    assert 'Hi Voila' in response.body.decode('utf-8')
