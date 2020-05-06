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
    return base_url + "voila/render/print.ipynb"


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'print.ipynb')


@pytest.fixture(autouse=1)
def get_jupyter_kernels(env_jupyter_path):
    src = sys.prefix + '/share/jupyter/kernels'
    dst = str(env_jupyter_path) + '/kernels'
    shutil.copytree(src, dst)


@pytest.fixture(autouse=1)
def get_nbconvert_templates(env_jupyter_path):
    src = sys.prefix + '/share/jupyter/nbconvert'
    dst = str(env_jupyter_path) + '/nbconvert'
    shutil.copytree(src, dst)


@pytest.fixture(autouse=1)
def get_voila_templates(env_jupyter_path):
    src = sys.prefix + '/share/jupyter/voila'
    dst = str(env_jupyter_path) + '/voila'
    shutil.copytree(src, dst)


@pytest.fixture(autouse=1)
def get_nbextensions(env_jupyter_path):
    src = sys.prefix + '/share/jupyter/nbextensions'
    dst = str(env_jupyter_path) + '/nbextensions'
    shutil.copytree(src, dst)
