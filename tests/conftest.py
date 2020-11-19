# fixtures common for app and server
import os

import pytest


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def notebook_directory():
    return os.path.join(BASE_DIR, 'notebooks')


@pytest.fixture
def print_notebook_url(base_url):
    return base_url + "voila/render/print.ipynb"


@pytest.fixture
def syntax_error_notebook_url(base_url):
    return base_url + "voila/render/syntax_error.ipynb"


@pytest.fixture
def exception_runtime_notebook_url(base_url):
    return base_url + "voila/render/exception_runtime.ipynb"


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'print.ipynb')


# this forces the event_loop fixture in pytest_asyncio to use the same ioloop as pytest_tornasync
@pytest.fixture()
def event_loop(io_loop):
    import asyncio
    return asyncio.get_event_loop()
