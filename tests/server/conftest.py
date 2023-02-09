import os

import pytest

from jupyter_server.serverapp import ServerApp
from jupyter_server.services.contents.largefilemanager import LargeFileManager

from tornado import httpserver


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def jupyter_server_config():
    return lambda app: None


@pytest.fixture
def jupyter_server_args_extra():
    return []


@pytest.fixture
def jupyter_server_args(notebook_directory, jupyter_server_args_extra):
    debug_args = ['--ServerApp.log_level=DEBUG'] if os.environ.get('VOILA_TEST_DEBUG', False) else []
    default_args = ['--ServerApp.token=']
    return [notebook_directory] + jupyter_server_args_extra + debug_args + default_args


@pytest.fixture
def jupyter_server_app(jupyter_server_args, jupyter_server_config):
    jupyter_server_app = ServerApp.instance()

    # TODO: I'm not sure if this is the right thing to do or make treehandler deal with both sync and async contents_managers? 
    jupyter_server_app.contents_manager_class=LargeFileManager
    # we monkey patch
    old_listen = httpserver.HTTPServer.listen
    httpserver.HTTPServer.listen = lambda *x, **y: None
    # NOTE: in voila's conftest.py we call config after initialize
    jupyter_server_config(jupyter_server_app)
    jupyter_server_app.initialize(jupyter_server_args)
    yield jupyter_server_app
    httpserver.HTTPServer.listen = old_listen
    ServerApp.clear_instance()


@pytest.fixture
def app(jupyter_server_app):
    return jupyter_server_app.web_app
