import pytest

NOTEBOOK_PATH = 'syntax_error.ipynb'


@pytest.fixture(params=[True, False])
def show_tracebacks(request):
    return request.param


@pytest.fixture
def notebook_show_traceback_path(base_url):
    return base_url + f'voila/render/{NOTEBOOK_PATH}'


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra, show_tracebacks):
    return [
        '--VoilaTest.root_dir=%r' % notebook_directory,
        f'--VoilaConfiguration.show_tracebacks={show_tracebacks}',
    ] + voila_args_extra


async def test_syntax_error(
    http_server_client, notebook_show_traceback_path, show_tracebacks
):

    response = await http_server_client.fetch(notebook_show_traceback_path)
    assert response.code == 200
    output = response.body.decode('utf-8')
    if show_tracebacks:
        assert 'this is a syntax error' in output, 'should show the "code"'
        assert (
            'SyntaxError' in output and 'invalid syntax' in output
        ), 'should show the error'
    else:
        assert 'There was an error when executing cell' in output
        assert 'This should not be executed' not in output
