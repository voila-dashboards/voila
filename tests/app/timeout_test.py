import os

import pytest


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, "sleep.ipynb")


@pytest.fixture
def voila_args_extra():
    return ["--VoilaExecutor.timeout=1", "--KernelManager.shutdown_wait_time=0.1"]


async def test_timeout(http_server_client, base_url):
    response = await http_server_client.fetch(base_url)
    html_text = response.body.decode("utf-8")
    assert "Cell execution timed out" in html_text
