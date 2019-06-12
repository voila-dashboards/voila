# tests the --template argument of voila
import pytest


@pytest.fixture
def voila_args_extra():
    return ['--template=test_template']


@pytest.mark.gen_test
def test_template(http_client, base_url):
    response = yield http_client.fetch(base_url)
    assert response.code == 200
    assert 'test_template.css' in response.body.decode('utf-8')
    assert 'Hi Voila' in response.body.decode('utf-8')
