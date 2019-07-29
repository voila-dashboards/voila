import pytest


@pytest.fixture
def non_existing_kernel_notebook(base_url):
    return base_url + "/voila/render/non_existing_kernel.ipynb"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--VoilaTest.root_dir=%r' % notebook_directory] + voila_args_extra


@pytest.mark.gen_test
def test_non_existing_kernel(http_client, non_existing_kernel_notebook):
    response = yield http_client.fetch(non_existing_kernel_notebook)
    assert response.code == 200
    assert 'non-existing kernel' in response.body.decode('utf-8')
