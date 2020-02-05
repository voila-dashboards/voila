import os
import pytest


@pytest.fixture
def voila_args_extra():
    return ['--ExecutePreprocessor.timeout=180']


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'many_iopub_messages.ipynb')


@pytest.mark.gen_test
def test_template_cwd(http_client, base_url, notebook_directory):
    response = yield http_client.fetch(base_url)
    html_text = response.body.decode('utf-8')
    assert 'you should see me' in html_text
