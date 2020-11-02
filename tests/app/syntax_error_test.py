import pytest


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--VoilaTest.root_dir=%r' % notebook_directory] + voila_args_extra


async def test_syntax_error(capsys, http_server_client, syntax_error_notebook_url):
    response = await http_server_client.fetch(syntax_error_notebook_url)
    assert response.code == 200
    output = response.body.decode('utf-8')
    assert 'There was an error when executing cell' in output
    assert 'This should not be executed' not in output
