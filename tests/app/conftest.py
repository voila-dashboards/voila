import os

import pytest

import voila.app

BASE_DIR = os.path.dirname(__file__)


class VoilaTest(voila.app.Voila):
    def listen(self):
        pass  # the ioloop is taken care of by the pytest-tornado framework


@pytest.fixture
def voila_config():
    return lambda app: None


@pytest.fixture
def voila_args_extra():
    return []


@pytest.fixture
def voila_config_file_paths_arg():
    # we don't want the tests to use any configuration on the system
    return '--VoilaTest.config_file_paths=[]'


@pytest.fixture
def voila_args(voila_notebook, voila_args_extra, voila_config_file_paths_arg):
    debug_args = ['--VoilaTest.log_level=DEBUG'] if os.environ.get('VOILA_TEST_DEBUG', False) else []
    return [voila_notebook, voila_config_file_paths_arg] + voila_args_extra + debug_args


@pytest.fixture
def voila_app(voila_args, voila_config):
    server_app = VoilaTest.initialize_server(argv=['--ServerApp.open_browser=False'])
    voila_app = VoilaTest._prepare_launch(server_app, argv=voila_args)
    voila_config(voila_app)
    voila_app.start_server()
    yield voila_app
    server_app.stop()
    server_app.clear_instance()
    voila_app.clear_instance()
