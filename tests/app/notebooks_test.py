# simply tests if some notebooks execute
import pytest
import os

NOTEBOOK_PATH = 'other_comms.ipynb'


@pytest.fixture
def notebook_other_comms_path(base_url, preheat_mode):
    if preheat_mode:
        return base_url
    return base_url + f'voila/render/{NOTEBOOK_PATH}'


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra, preheat_mode):
    if preheat_mode:
        return [
            os.path.join(notebook_directory,NOTEBOOK_PATH),
            '--VoilaTest.log_level=DEBUG',
        ] + voila_args_extra
    return [
        '--VoilaTest.root_dir=%r' % notebook_directory,
        '--VoilaTest.log_level=DEBUG',
    ] + voila_args_extra


async def test_other_comms(
    http_server_client, notebook_other_comms_path, wait_for_kernel
):
    await wait_for_kernel()
    response = await http_server_client.fetch(notebook_other_comms_path)
    html_text = response.body.decode('utf-8')
    assert 'This notebook executed' in html_text
