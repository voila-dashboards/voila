import os
import pytest

TEST_XEUS_CLING = os.environ.get('VOILA_TEST_XEUS_CLING', '') == '1'


@pytest.fixture
def voila_args_extra():
    return ['--Voila.extension_language_mapping={".xcpp": "C++11"}']


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--Voila.root_dir=%r' % notebook_directory] + voila_args_extra + ['--no-browser']


@pytest.mark.skipif(not TEST_XEUS_CLING, reason='opt in to avoid having to install xeus-cling')
async def test_cpp11_kernel(fetch, get_jupyter_kernels):
    response = await fetch('voila', 'render', 'print.xcpp', method='GET')
    assert response.code == 200
    assert 'Hello voila, from c++' in response.body.decode('utf-8')
