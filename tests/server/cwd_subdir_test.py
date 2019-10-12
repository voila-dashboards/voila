# NOTE: this is a duplicate of ../app/cwd_subdir_test.py
# we might want to find a better pattern of executing test for the app and extension
import pytest


@pytest.fixture
def cwd_subdir_notebook_url(base_url):
    return f"{base_url}/voila/render/subdir/cwd_subdir.ipynb"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return [f'--VoilaTest.root_dir={notebook_directory!r}', '--VoilaTest.log_level=DEBUG'] + voila_args_extra


@pytest.mark.gen_test
def test_hello_world(http_client, cwd_subdir_notebook_url):
    response = yield http_client.fetch(cwd_subdir_notebook_url)
    html_text = response.body.decode('utf-8')
    assert 'check for the cwd' in html_text
