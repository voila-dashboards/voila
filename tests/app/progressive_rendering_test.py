import asyncio
import os
import time

import pytest


@pytest.fixture
def progressive_rendering_mode():
    return True


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, "preheat", "pre_heat.ipynb")


NOTEBOOK_EXECUTION_TIME = 2
TIME_THRESHOLD = NOTEBOOK_EXECUTION_TIME


async def send_request(sc, url, wait=0):
    await asyncio.sleep(wait)
    real_time = time.time()
    response = await sc.fetch(url)
    real_time = time.time() - real_time
    html_text = response.body.decode("utf-8")
    return real_time, html_text


async def test_request(http_server_client, base_url):
    """
    We send a request to server immediately, the returned HTML should
    not contain the output.
    """
    time, text = await send_request(sc=http_server_client, url=base_url)
    assert '"progressiveRendering": true' in text
    assert "hello world" not in text
    assert time < NOTEBOOK_EXECUTION_TIME
