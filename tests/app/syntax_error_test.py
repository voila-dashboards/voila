import os

import pytest

NOTEBOOK_PATH = "syntax_error.ipynb"


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, NOTEBOOK_PATH)


async def test_syntax_error(http_server_client, base_url):
    response = await http_server_client.fetch(base_url)
    assert response.code == 200
    output = response.body.decode("utf-8")
    assert "There was an error when executing cell" in output
    assert "This should not be executed" not in output
