# test serving a notebook or python/c++ notebook
import os

import pytest

TEST_XEUS_CLING = os.environ.get("VOILA_TEST_XEUS_CLING", "") == "1"


@pytest.fixture
def preheat_mode():
    return False


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ["--VoilaTest.root_dir=%r" % notebook_directory, *voila_args_extra]


async def test_print(http_server_client, print_notebook_url):
    print(print_notebook_url)
    response = await http_server_client.fetch(print_notebook_url)
    assert response.code == 200
    assert "Hi Voilà" in response.body.decode("utf-8")


@pytest.fixture
def voila_args_extra():
    return ['--VoilaConfiguration.extension_language_mapping={".py": "python"}']


async def test_print_py(http_server_client, print_notebook_url):
    print(print_notebook_url)
    response = await http_server_client.fetch(print_notebook_url.replace("ipynb", "py"))
    assert response.code == 200
    assert "Hi Voilà" in response.body.decode("utf-8")


@pytest.mark.skipif(
    not TEST_XEUS_CLING, reason="opt in to avoid having to install xeus-cling"
)
async def test_print_julia_notebook(http_server_client, print_notebook_url):
    print(print_notebook_url)
    response = await http_server_client.fetch(
        print_notebook_url.replace(".ipynb", "_cpp.ipynb")
    )
    assert response.code == 200
    assert "Hi Voilà, from c++" in response.body.decode("utf-8")
