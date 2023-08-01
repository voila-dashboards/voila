# fixtures common for app and server
import os
import time

import pytest

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def base_url():
    return "/"


@pytest.fixture
def notebook_directory():
    return os.path.join(BASE_DIR, "notebooks")


@pytest.fixture
def print_notebook_url(base_url):
    return base_url + "voila/render/print.ipynb"


@pytest.fixture
def syntax_error_notebook_url(base_url):
    return base_url + "voila/render/syntax_error.ipynb"


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, "print.ipynb")


@pytest.fixture(autouse=True)
def sleep_between_tests():
    yield
    time.sleep(1)
