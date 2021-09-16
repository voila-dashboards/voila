# tests the --template argument of voila
import pytest

import os


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'cwd.ipynb')


async def test_template_cwd(http_server_client, base_url, wait_for_kernel):
    await wait_for_kernel()
    response = await http_server_client.fetch(base_url)
    html_text = response.body.decode('utf-8')
    assert 'check for the cwd' in html_text
