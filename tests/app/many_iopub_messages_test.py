import os
import pytest
import tornado.httpclient

MAX_TIMEOUT_SECONDS = 240


@pytest.fixture
def voila_args_extra():
    return [f'--VoilaExecutor.timeout={MAX_TIMEOUT_SECONDS}']


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'many_iopub_messages.ipynb')


@pytest.fixture
def http_client(request, http_server):
    """Get an asynchronous HTTP client.
    """
    client = tornado.httpclient.AsyncHTTPClient(defaults=dict(request_timeout=MAX_TIMEOUT_SECONDS+20))

    def _close():
        client.close()

    request.addfinalizer(_close)
    return client


async def test_template_cwd(http_server_client, base_url, notebook_directory):
    response = await http_server_client.fetch(base_url)
    html_text = response.body.decode('utf-8')
    assert 'you should see me' in html_text
