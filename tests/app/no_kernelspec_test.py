import pytest


#@pytest.fixture
#def non_existing_kernel_notebook(base_url):
#    return base_url + "/voila/render/no_kernelspec.ipynb"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--Voila.root_dir=%r' % notebook_directory] + voila_args_extra


async def test_no_kernelspec(fetch, token):
    response = await fetch('voila', 'render', 'no_kernelspec.ipynb', params={'token': token}, method='GET')
    assert response.code == 200
    assert 'Executing without a kernelspec' in response.body.decode('utf-8')
