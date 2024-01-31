# tests the --template argument of Voilà
import pytest


@pytest.fixture
def voila_args_extra():
    return ["--template=test_template", "--VoilaExecutor.timeout=240"]


async def test_template(http_server_client, base_url):
    response = await http_server_client.fetch(base_url)
    assert response.code == 200
    assert "test_template.css" in response.body.decode("utf-8")
    assert "Hi Voilà" in response.body.decode("utf-8")
