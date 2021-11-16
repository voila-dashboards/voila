# tests prelaunch hook config
import pytest

import os

from nbformat import NotebookNode

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'print.ipynb')


@pytest.fixture
def voila_config():
    def foo(req, notebook, cwd):
        argument = req.get_argument("test")
        notebook.cells.append(NotebookNode({
            "cell_type": "code",
            "execution_count": 0,
            "metadata": {},
            "outputs": [],
            "source": f"print(\"Hi prelaunch hook {argument}!\")\n"
        }))

    def config(app):
        app.prelaunch_hook = foo
    return config


async def test_prelaunch_hook(http_server_client, base_url):
    response = await http_server_client.fetch(base_url + "?test=blerg", )
    assert response.code == 200
    assert 'Hi Voilà' in response.body.decode('utf-8')
    assert 'Hi prelaunch hook blerg' in response.body.decode('utf-8')
