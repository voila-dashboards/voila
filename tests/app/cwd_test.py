# tests the --template argument of voila
import pytest
import base64
import os

@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'cwd.ipynb')


@pytest.mark.gen_test
def test_template_cwd(http_client, base_url, notebook_directory):
    response = yield http_client.fetch(base_url)
    html_text = response.body.decode('utf-8')
    assert 'check for the cwd' in html_text

