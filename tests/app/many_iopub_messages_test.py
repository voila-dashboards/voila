import os
import pytest

MAX_TIMEOUT_SECONDS = 240


@pytest.fixture
def preheat_mode():
    return False

@pytest.fixture
def voila_args_extra():
    return [f'--VoilaExecutor.timeout={MAX_TIMEOUT_SECONDS}']


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'many_iopub_messages.ipynb')


async def test_template_cwd(http_server_client, base_url, wait_for_kernel):
    await wait_for_kernel(10)
    response = await http_server_client.fetch(base_url, request_timeout=MAX_TIMEOUT_SECONDS+20)
    html_text = response.body.decode('utf-8')
    assert 'you should see me' in html_text
