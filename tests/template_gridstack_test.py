# tests the --template argument of voila
import pytest


@pytest.fixture
def voila_args_extra():
    return ['--template=gridstack']


@pytest.mark.gen_test
def test_template_gridstack(http_client, base_url):
    response = yield http_client.fetch(base_url)
    assert response.code == 200
    assert 'gridstack.css' in response.body.decode('utf-8')
    assert 'Hi Voila' in response.body.decode('utf-8')
