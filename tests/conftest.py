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
def voila_notebook():
    return os.path.join(BASE_DIR, 'notebooks/print.ipynb')


@pytest.fixture
def voila_args_extra():
    return []


@pytest.fixture
def voila_args(voila_notebook, voila_args_extra):
    debug_args = ['--VoilaTest.log_level=DEBUG'] if os.environ.get('VOILA_TEST_DEBUG', False) else []
    return [voila_notebook] + voila_args_extra + debug_args


@pytest.fixture
def voila_app(voila_args, voila_config):
    voila_app = VoilaTest.instance()
    voila_app.initialize(voila_args)
    voila_config(voila_app)
    voila_app.start()
    return voila_app


@pytest.fixture
def app(voila_app):
    return voila_app.app


