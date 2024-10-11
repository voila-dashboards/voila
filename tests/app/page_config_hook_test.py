import os

import pytest


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, "print.ipynb")


@pytest.fixture
def voila_config():
    def foo(current_page_config, **kwargs):
        current_page_config["foo"] = "my custom config"
        return current_page_config

    def config(app):
        app.voila_configuration.page_config_hook = foo

    return config


async def test_prelaunch_hook(http_server_client, base_url):
    response = await http_server_client.fetch(base_url)
    assert response.code == 200
    assert "my custom config" in response.body.decode("utf-8")
