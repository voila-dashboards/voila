# tests basic things the templates should have
import os

import pytest

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture(params=["lab", "classic"])
def voila_args_extra(request):
    return [f"--template={request.param}"]


async def test_lists_extension(http_server_client, base_url, voila_app):
    response = await http_server_client.fetch(base_url)
    assert response.code == 200
    html_text = response.body.decode("utf-8")
    assert "/voila/static/voila.js" in html_text
