import os
import pytest
import tornado.httpclient


@pytest.fixture
def voila_args_extra():
    return ['--ExecutePreprocessor.timeout=180']


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'many_iopub_messages.ipynb')


@pytest.fixture
def http_client(request, http_server):
    """Get an asynchronous HTTP client.
    """
    client = tornado.httpclient.AsyncHTTPClient(defaults=dict(request_timeout=200))

    def _close():
        client.close()

    request.addfinalizer(_close)
    return client


async def test_template_cwd(fetch, notebook_directory):
    response = await fetch('voila', method='GET')
    html_text = response.body.decode('utf-8')
    assert 'you should see me' in html_text
