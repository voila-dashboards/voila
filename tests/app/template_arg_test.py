# tests the --template argument of voila
import pytest


@pytest.fixture
def voila_args_extra():
    return ['--template=test_template']


async def test_template(fetch, token):
    response = await fetch('voila', params={'token': token}, method='GET')
    assert response.code == 200
    assert 'test_template.css' in response.body.decode('utf-8')
    assert 'Hi Voila' in response.body.decode('utf-8')
