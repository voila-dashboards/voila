import pytest


@pytest.fixture(params=[True, False])
def show_tracebacks(request):
    return request.param


@pytest.fixture
def jupyter_server_args_extra(show_tracebacks):
    return [f"--VoilaConfiguration.show_tracebacks={show_tracebacks}"]


async def test_syntax_error(
    http_server_client, syntax_error_notebook_url, show_tracebacks
):
    response = await http_server_client.fetch(syntax_error_notebook_url)
    assert response.code == 200
    output = response.body.decode("utf-8")
    if show_tracebacks:
        assert "this is a syntax error" in output, 'should show the "code"'
        assert (
            "SyntaxError" in output and "invalid syntax" in output
        ), "should show the error"
    else:
        assert "There was an error when executing cell" in output
        assert "This should not be executed" not in output
