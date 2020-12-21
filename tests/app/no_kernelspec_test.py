import pytest


@pytest.fixture
def non_existing_kernel_notebook(jp_base_url):
    return jp_base_url + "voila/render/no_kernelspec.ipynb"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--VoilaTest.root_dir=%r' % notebook_directory] + voila_args_extra


async def test_non_existing_kernel(http_server_client, non_existing_kernel_notebook):
    response = await http_server_client.fetch(non_existing_kernel_notebook)
    assert response.code == 200
    assert 'Executing without a kernelspec' in response.body.decode('utf-8')
