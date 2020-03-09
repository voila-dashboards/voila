# test serving a notebook
import pytest


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--ServerApp.root_dir=%r' % notebook_directory, '--Voila.log_level=DEBUG'] + voila_args_extra


async def test_hello_world(fetch, token):
    response = await fetch('voila', 'render', 'subdir', 'cwd_subdir.ipynb', params={'token': token}, method='GET')
    html_text = response.body.decode('utf-8')
    assert 'check for the cwd' in html_text
