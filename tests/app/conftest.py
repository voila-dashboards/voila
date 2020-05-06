import os

import pytest

from voila.app import Voila

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_config(notebook_directory):
    return dict(root_dir=notebook_directory)


@pytest.fixture
def server_config(notebook_directory):
    return dict(root_dir=notebook_directory, default_url="voila", log_level="DEBUG")


@pytest.fixture
def voila_args_extra():
    return []


@pytest.fixture
def voila_config_file_paths_arg():
    # we don't want the tests to use any configuration on the system
    return '--Voila.config_file_paths=[]'


@pytest.fixture
def voila_args(voila_notebook, voila_args_extra, voila_config_file_paths_arg):
    debug_args = ['--Voila.log_level=DEBUG'] if os.environ.get('VOILA_TEST_DEBUG', False) else []
    return [voila_notebook, voila_config_file_paths_arg] + voila_args_extra + debug_args + ['--no-browser']


@pytest.fixture(autouse=True)
def voila_app(server_config, voila_config, voila_args, get_nbconvert_template):
    # Get an instance of Voila
    voila_app = Voila(**voila_config)
    # Get an instance of the underlying server. This is
    # configured automatically when launched by command line.
    serverapp = voila_app.initialize_server(voila_args, **server_config)
    # silence the start method for pytests.
    serverapp.start = lambda self: None
    voila_app.link_to_serverapp(serverapp)
    voila_app.initialize()
    yield voila_app
    serverapp.cleanup_kernels()
    serverapp.clear_instance()
