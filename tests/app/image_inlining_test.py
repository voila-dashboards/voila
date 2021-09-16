# tests the --template argument of voila
import pytest

import base64

import os

NOTEBOOK_PATH = 'images.ipynb'

@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, NOTEBOOK_PATH)


async def test_image_inlining(http_server_client, base_url, notebook_directory, wait_for_kernel):
    await wait_for_kernel()
    response = await http_server_client.fetch(base_url)
    html_text = response.body.decode('utf-8')

    assert 'data:image/svg+xml;base64,' in html_text
    assert 'data:image/png;base64,' in html_text

    # check if the external file is inline
    with open(os.path.join(notebook_directory, notebook_directory, 'jupyter.svg'), 'rb') as f:
        svg_data = f.read()
    svg_data_base64 = base64.b64encode(svg_data).decode('ascii')
    assert svg_data_base64 in html_text
