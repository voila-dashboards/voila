import pytest

NOTEBOOK_PATH = 'cgi.ipynb'

@pytest.fixture
def notebook_cgi_path(base_url, preheat_mode):
    if preheat_mode:
        return base_url
    return base_url + f"voila/render/{NOTEBOOK_PATH}"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra, preheat_mode):
    if preheat_mode:
        return [f'{notebook_directory}/{NOTEBOOK_PATH}', '--VoilaTest.log_level=DEBUG'] + voila_args_extra
    else:
        return ['--VoilaTest.root_dir=%r' % notebook_directory, '--VoilaTest.log_level=DEBUG'] + voila_args_extra


async def test_cgi_using_query_parameters(capsys, http_server_client, notebook_cgi_path, wait_for_kernel):
    await wait_for_kernel()
    response = await http_server_client.fetch(notebook_cgi_path + '?username=VOILA')
    assert response.code == 200
    assert 'VOILA' in response.body.decode('utf-8')
