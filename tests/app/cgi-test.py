import pytest


@pytest.fixture
def notebook_cgi_path(base_url):
    return base_url + "voila/render/cgi.ipynb"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--VoilaTest.root_dir=%r' % notebook_directory, '--VoilaTest.log_level=DEBUG'] + voila_args_extra


async def test_cgi_using_query_parameters(capsys, http_server_client, notebook_cgi_path):
    response = await http_server_client.fetch(notebook_cgi_path + '?username=VOILA')
    assert response.code == 200
    assert 'VOILA' in response.body.decode('utf-8')
