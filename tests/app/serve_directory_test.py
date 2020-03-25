# test serving a notebook or python/c++ notebook
import os
import pytest

TEST_XEUS_CLING = os.environ.get('VOILA_TEST_XEUS_CLING', '') == '1'


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ["--Voila.root_dir=%r" % notebook_directory] + voila_args_extra


async def test_print(fetch, token):
    response = await fetch('voila', 'render', 'print.ipynb', params={'token': token}, method='GET')
    assert response.code == 200
    assert 'Hi Voila' in response.body.decode('utf-8')


@pytest.fixture
def voila_args_extra():
    return ['--Voila.extension_language_mapping={".py": "python"}']


async def test_print_py(fetch, token):
    response = await fetch('voila', 'render', 'print.py', params={'token': token}, method='GET')
    assert response.code == 200
    assert 'Hi Voila' in response.body.decode('utf-8')


@pytest.mark.skipif(not TEST_XEUS_CLING, reason='opt in to avoid having to install xeus-cling')
async def test_print_cpp_notebook(fetch, token, jupyter_kernels):
    response = await fetch('voila', 'render', 'print_cpp.ipynb', params={'token': token}, method='GET')
    assert response.code == 200
    assert 'Hi Voila, from c++' in response.body.decode('utf-8')
