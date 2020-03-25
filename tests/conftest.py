# fixtures common for app and server
import os
import pytest
import shutil
import sys


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def notebook_directory():
    return os.path.join(BASE_DIR, 'notebooks')


@pytest.fixture
def print_notebook_url(base_url):
    return base_url + "/voila/render/print.ipynb"


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'print.ipynb')


@pytest.fixture
def jupyter_kernels(env_jupyter_path):
    src = sys.prefix + '/share/jupyter/kernels'
    dst = str(env_jupyter_path) + '/kernels'
    shutil.copytree(src, dst)
