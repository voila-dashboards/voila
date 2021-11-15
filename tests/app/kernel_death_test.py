import pytest

import os


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'autokill.ipynb')


@pytest.fixture
def voila_args_extra():
    return ['--debug']


@pytest.fixture
def preheat_mode():
    return False


async def test_kernel_death(http_server_client, base_url):

    response = await http_server_client.fetch(base_url)
    html_text = response.body.decode('utf-8')
    assert 'raise DeadKernelError' in html_text
