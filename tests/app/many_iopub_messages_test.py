import os
import pytest

MAX_TIMEOUT_SECONDS = 240


@pytest.fixture
def voila_args_extra():
    return [f'--VoilaExecutor.timeout={MAX_TIMEOUT_SECONDS}']


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'many_iopub_messages.ipynb')


async def test_template_cwd(http_server_client, jp_base_url, notebook_directory):
    response = await http_server_client.fetch(jp_base_url, request_timeout=MAX_TIMEOUT_SECONDS+20)
    html_text = response.body.decode('utf-8')
    assert 'you should see me' in html_text
