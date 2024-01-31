# tests the --template argument of voila
import os

import pytest


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, "cwd.ipynb")


async def test_template_cwd(http_server_client, base_url):
    response = await http_server_client.fetch(base_url)
    html_text = response.body.decode("utf-8")
    assert "check for the cwd" in html_text
