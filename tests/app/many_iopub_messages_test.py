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


#@pytest.mark.gen_test
async def test_template_cwd(http_client, base_url, notebook_directory):
    response = yield http_client.fetch(base_url)
    html_text = response.body.decode('utf-8')
    assert 'you should see me' in html_text
