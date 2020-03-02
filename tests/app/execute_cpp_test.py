import os
import pytest

TEST_XEUS_CLING = os.environ.get('VOILA_TEST_XEUS_CLING', '') == '1'


@pytest.fixture
def cpp_file_url(base_url, add_token):
    return add_token(base_url + "/voila/render/print.xcpp")


@pytest.fixture
def voila_args_extra():
    return ['--Voila.extension_language_mapping={".xcpp": "C++11"}']


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--Voila.root_dir=%r' % notebook_directory] + voila_args_extra


@pytest.mark.skipif(not TEST_XEUS_CLING, reason='opt in to avoid having to install xeus-cling')
async def test_non_existing_kernel(http_client, cpp_file_url):
    response = yield http_client.fetch(cpp_file_url)
    assert response.code == 200
    assert 'Hello voila, from c++' in response.body.decode('utf-8')
