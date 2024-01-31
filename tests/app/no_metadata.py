import pytest

NOTEBOOK_PATH = "no_metadata.ipynb"


@pytest.fixture
def non_existing_notebook_metadata(base_url):
    return base_url + f"voila/render/{NOTEBOOK_PATH}"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return [f"--VoilaTest.root_dir={notebook_directory!r}", *voila_args_extra]


async def test_non_existing_metadata(
    http_server_client, non_existing_notebook_metadata
):
    response = await http_server_client.fetch(non_existing_notebook_metadata)
    assert response.code == 200
    assert "Executing without notebook metadata" in response.body.decode("utf-8")
