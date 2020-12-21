# fixtures common for app and server
import os

import pytest


BASE_DIR = os.path.dirname(__file__)

pytest_plugins = [
    "jupyter_server.pytest_plugin",
]

@pytest.fixture
def notebook_directory():
    return os.path.join(BASE_DIR, 'notebooks')


@pytest.fixture
def print_notebook_url(jp_base_url):
    return jp_base_url + "voila/render/print.ipynb"


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'print.ipynb')
