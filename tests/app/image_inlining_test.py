# tests the --template argument of voila
import pytest

import base64

import os


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'images.ipynb')


async def test_image_inlining(fetch, notebook_directory):
    response = await fetch('voila', method='GET')
    html_text = response.body.decode('utf-8')

    assert 'data:image/svg+xml;base64,' in html_text
    assert 'data:image/png;base64,' in html_text

    # check if the external file is inline
    with open(os.path.join(notebook_directory, notebook_directory, 'jupyter.svg'), 'rb') as f:
        svg_data = f.read()
    svg_data_base64 = base64.b64encode(svg_data).decode('ascii')
    assert svg_data_base64 in html_text
