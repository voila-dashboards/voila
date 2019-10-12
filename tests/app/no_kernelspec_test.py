import pytest


@pytest.fixture
def non_existing_kernel_notebook(base_url):
    return f"{base_url}/voila/render/no_kernelspec.ipynb"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return [f'--VoilaTest.root_dir={notebook_directory!r}'] + voila_args_extra


@pytest.mark.gen_test
def test_non_existing_kernel(http_client, non_existing_kernel_notebook):
    response = yield http_client.fetch(non_existing_kernel_notebook)
    assert response.code == 200
    assert 'Executing without a kernelspec' in response.body.decode('utf-8')
