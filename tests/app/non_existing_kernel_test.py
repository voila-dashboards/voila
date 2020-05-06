import pytest


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--Voila.root_dir=%r' % notebook_directory] + voila_args_extra + ['--no-browser']


async def test_non_existing_kernel(fetch):
    response = await fetch('voila', 'render', 'non_existing_kernel.ipynb', method='GET')
    assert response.code == 200
    assert 'non-existing kernel' in response.body.decode('utf-8')
