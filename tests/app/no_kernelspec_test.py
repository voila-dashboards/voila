import pytest

NOTEBOOK_PATH = "no_kernelspec.ipynb"


@pytest.fixture
def non_existing_kernel_notebook(base_url):
    return base_url + f"voila/render/{NOTEBOOK_PATH}"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ["--VoilaTest.root_dir=%r" % notebook_directory] + voila_args_extra


async def test_non_existing_kernel(
    http_server_client,
    non_existing_kernel_notebook,
):
    response = await http_server_client.fetch(non_existing_kernel_notebook)
    assert response.code == 200
    assert "Executing without a kernelspec" in response.body.decode("utf-8")
