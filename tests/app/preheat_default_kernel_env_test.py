import asyncio
import os

import pytest


@pytest.fixture()
def voila_args_extra():
    return ['--VoilaKernelManager.default_env_variables={"FOO": "BAR"}']


@pytest.fixture
def preheat_mode():
    return True


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, "preheat", "default_env_variables.ipynb")


NOTEBOOK_EXECUTION_TIME = 2


async def send_request(sc, url, wait=0):
    await asyncio.sleep(wait)
    response = await sc.fetch(url)
    return response.body.decode("utf-8")


async def test_default_kernel_env_variable(http_server_client, base_url):
    html_text = await send_request(
        sc=http_server_client, url=base_url, wait=NOTEBOOK_EXECUTION_TIME + 1
    )
    assert "BAR" in html_text
