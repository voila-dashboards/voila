import pytest

import os


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'autokill.ipynb')


@pytest.fixture
def voila_args_extra():
    return ['--debug']


async def test_kernel_death(http_server_client, base_url, wait_for_kernel):
    await wait_for_kernel()
    response = await http_server_client.fetch(base_url)
    html_text = response.body.decode('utf-8')
    assert 'raise DeadKernelError' in html_text
