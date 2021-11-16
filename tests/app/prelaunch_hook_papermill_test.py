# tests prelaunch hook config
import pytest

import os

from nbformat import NotebookNode
from urllib.parse import quote_plus

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'print_parameterized.ipynb')


@pytest.fixture
def voila_config():
    def parameterize_with_papermill(req, notebook, cwd):
        import tornado

        # Grab parameters
        parameters = req.get_argument("parameters", {})

        # try to convert to dict if not e.g. string/unicode
        if not isinstance(parameters, dict):
            try:
                parameters = tornado.escape.json_decode(parameters)
            except ValueError:
                parameters = None

        # if passed and a dict, use papermill to inject parameters
        if parameters and isinstance(parameters, dict):
            from papermill.parameterize import parameterize_notebook

            # setup for papermill
            # 
            # these two blocks are done
            # to avoid triggering errors
            # in papermill's notebook
            # loading logic
            for cell in notebook.cells:
                if 'tags' not in cell.metadata:
                    cell.metadata.tags = []
                if "papermill" not in notebook.metadata:
                    notebook.metadata.papermill = {}

            # Parameterize with papermill
            return parameterize_notebook(notebook, parameters)

    def config(app):
        app.prelaunch_hook = parameterize_with_papermill

    return config


async def test_prelaunch_hook_papermill(http_server_client, base_url):
    url = base_url + '?parameters=' + quote_plus('{"name":"Parameterized_Variable"}')
    response = await http_server_client.fetch(url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Parameterized_Variable' in html_text
    assert 'test_template.css' not in html_text, "test_template should not be the default"
