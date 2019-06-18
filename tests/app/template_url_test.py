# tests selecting a template via query string parameters
import pytest


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--template=default', '--VoilaTest.root_dir=%r' % notebook_directory] + voila_args_extra


@pytest.mark.gen_test
def test_default_template(http_client, print_notebook_url):
    response = yield http_client.fetch(print_notebook_url)
    assert response.code == 200
    assert 'theme-light.css' in response.body.decode('utf-8')


@pytest.mark.gen_test
def test_template_url_parameter(http_client, print_notebook_url):
    url = print_notebook_url + "?template=test_template"
    response = yield http_client.fetch(url)
    assert response.code == 200
    assert 'test_template.css' in response.body.decode('utf-8')
