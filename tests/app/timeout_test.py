import pytest

import os


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'sleep.ipynb')


@pytest.fixture
def voila_args_extra():
    return ['--VoilaExecutePreprocessor.timeout=1', '--VoilaExecutePreprocessor.interrupt_on_timeout=True']#'--KernelManager.shutdown_wait_time=0.1']


async def test_timeout(fetch, token):
    response = await fetch('voila', params={'token': token}, method='GET')
    html_text = response.body.decode('utf-8')
    assert 'Cell execution timed out' in html_text
