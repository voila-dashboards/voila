# tests the --template argument of Voilà
import pytest
import os


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'skip-voila-cell.ipynb')


@pytest.fixture
def voila_args_extra():
    return ['--template=skip_template']


async def test_markdown_preprocessor(http_server_client, base_url, wait_for_kernel):
    await wait_for_kernel()
    response = await http_server_client.fetch(base_url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voilà cell' in html_text
    assert 'Hi non Voilà cell' not in html_text
