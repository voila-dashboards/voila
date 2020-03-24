import pytest


#@pytest.fixture
#def non_existing_kernel_notebook(base_url):
#    return base_url + "/voila/render/non_existing_kernel.ipynb"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--Voila.root_dir=%r' % notebook_directory] + voila_args_extra


async def test_non_existing_kernel(fetch, token):
    response = await fetch('voila', 'render', 'non_existing_kernel.ipynb', params={'token': token}, method='GET')
    assert response.code == 200
    assert 'non-existing kernel' in response.body.decode('utf-8')
