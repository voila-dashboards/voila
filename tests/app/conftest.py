import os
import urllib
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
    return [voila_notebook, voila_config_file_paths_arg] + voila_args_extra


@pytest.fixture
def voila_app(server_config, voila_config, voila_args):
    # Get an instance of Voila
    voila_app = Voila(**voila_config)
    # Get an instance of the underlying server. This is
    # configured automatically when launched by command line.
    serverapp = voila_app.initialize_server(voila_args, **server_config)
    # silence the start method for pytests.
    serverapp.start = lambda self: None
    voila_app.initialize(serverapp, argv=voila_args)
    yield voila_app
    serverapp.cleanup_kernels()
    serverapp.clear_instance()


@pytest.fixture
def token(voila_app):
    return voila_app.serverapp.token


@pytest.fixture
def app(voila_app):
    return voila_app.serverapp.web_app


@pytest.fixture
def add_token(voila_app):
    """Add a token to any url."""

    def add_token_to_url(url):
        parts = list(urllib.parse.urlparse(url))
        if parts[4] == "":
            query = "token={}".format(voila_app.serverapp.token)
        else:
            query = "{q}&token={token}".format(
                q=parts[4], token=voila_app.serverapp.token
            )
        parts[4] = query
        new_url = urllib.parse.urlunparse(parts)
        return new_url

    return add_token_to_url


@pytest.fixture
def default_url(base_url, add_token):
    print('base_url')
    print(base_url)
    return add_token(base_url)
