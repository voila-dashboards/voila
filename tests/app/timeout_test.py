import pytest

import os


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'sleep.ipynb')


@pytest.fixture
def voila_args_extra():
    return ['--VoilaExecutePreprocessor.timeout=1']


@pytest.mark.gen_test
def test_timeout(http_client, base_url):
    response = yield http_client.fetch(base_url)
    html_text = response.body.decode('utf-8')
    assert 'Cell execution timed out' in html_text
