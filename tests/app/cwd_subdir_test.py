# test serving a notebook
import pytest
import asyncio


NOTEBOOK_PATH = 'subdir/cwd_subdir.ipynb'
@pytest.fixture
def cwd_subdir_notebook_url(base_url, preheat_mode):
    if preheat_mode:
        return base_url
    return base_url + f'voila/render/{NOTEBOOK_PATH}'


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra, preheat_mode):
    if preheat_mode:
        return [f'{notebook_directory}/{NOTEBOOK_PATH}', '--VoilaTest.log_level=DEBUG'] + voila_args_extra
    else:
        return ['--VoilaTest.root_dir=%r' % notebook_directory, '--VoilaTest.log_level=DEBUG'] + voila_args_extra

async def test_hello_world(http_server_client, cwd_subdir_notebook_url, wait_for_kernel):
    await wait_for_kernel()
    response = await http_server_client.fetch(cwd_subdir_notebook_url)
    html_text = response.body.decode('utf-8')
    assert 'check for the cwd' in html_text
