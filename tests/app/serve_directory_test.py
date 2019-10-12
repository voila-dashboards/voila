# test serving a notebook or python/c++ notebook
import os
import pytest

TEST_XEUS_CLING = os.environ.get('VOILA_TEST_XEUS_CLING', '') == '1'


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return [f'--VoilaTest.root_dir={notebook_directory!r}', '--VoilaTest.log_level=DEBUG'] + voila_args_extra


@pytest.mark.gen_test
def test_print(http_client, print_notebook_url):
    print(print_notebook_url)
    response = yield http_client.fetch(print_notebook_url)
    assert response.code == 200
    assert 'Hi Voila' in response.body.decode('utf-8')


@pytest.fixture
def voila_args_extra():
    return ['--VoilaConfiguration.extension_language_mapping={".py": "python"}']


@pytest.mark.gen_test
def test_print_py(http_client, print_notebook_url):
    print(print_notebook_url)
    response = yield http_client.fetch(print_notebook_url.replace('ipynb', 'py'))
    assert response.code == 200
    assert 'Hi Voila' in response.body.decode('utf-8')


@pytest.mark.skipif(not TEST_XEUS_CLING, reason='opt in to avoid having to install xeus-cling')
@pytest.mark.gen_test
def test_print_julia_notebook(http_client, print_notebook_url):
    print(print_notebook_url)
    response = yield http_client.fetch(print_notebook_url.replace('.ipynb', '_cpp.ipynb'))
    assert response.code == 200
    assert 'Hi Voila, from c++' in response.body.decode('utf-8')
