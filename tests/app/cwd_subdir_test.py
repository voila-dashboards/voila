# test serving a notebook
import pytest

NOTEBOOK_PATH = "subdir/cwd_subdir.ipynb"


@pytest.fixture
def cwd_subdir_notebook_url(base_url):
    return base_url + f"voila/render/{NOTEBOOK_PATH}"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ["--VoilaTest.root_dir=%r" % notebook_directory, *voila_args_extra]


async def test_hello_world(http_server_client, cwd_subdir_notebook_url):
    response = await http_server_client.fetch(cwd_subdir_notebook_url)
    html_text = response.body.decode("utf-8")
    assert "check for the cwd" in html_text
