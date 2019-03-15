# test serving a notebook
import pytest

@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--VoilaTest.root_dir=%r' % notebook_directory, '--VoilaTest.log_level=DEBUG'] + voila_args_extra


@pytest.mark.gen_test
def test_hello_world(http_client, print_notebook_url):
    print(print_notebook_url)
    response = yield http_client.fetch(print_notebook_url)
    assert response.code == 200
    assert 'Hi Voila' in response.body.decode('utf-8')

