import asyncio
import os
import time

import pytest

BASE_DIR = os.path.dirname(__file__)
NOTEBOOK_EXECUTION_TIME = 3
NUMBER_PREHEATED_KERNEL = 2
TIME_THRESHOLD = 1


@pytest.fixture
def voila_config_file_paths_arg():
    path = os.path.join(BASE_DIR, "..", "configs", "preheat")
    return "--VoilaTest.config_file_paths=[%r]" % path


@pytest.fixture
def preheat_mode():
    return True


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, "preheat", "pre_heat.ipynb")


async def send_request(sc, url, wait=0):
    await asyncio.sleep(wait)
    real_time = time.time()
    response = await sc.fetch(url)
    real_time = time.time() - real_time
    html_text = response.body.decode("utf-8")
    return real_time, html_text


async def test_refill_kernel_asynchronously(http_server_client, base_url):
    await asyncio.sleep(NUMBER_PREHEATED_KERNEL * NOTEBOOK_EXECUTION_TIME + 1)
    fast = []
    slow = []
    for _i in range(5 * NUMBER_PREHEATED_KERNEL):
        time, _ = await send_request(sc=http_server_client, url=base_url)
        if time < TIME_THRESHOLD:
            fast.append(time)
        else:
            slow.append(time)

    assert len(fast) > 1
    assert len(slow) > 1
    assert len(fast) + len(slow) == 5 * NUMBER_PREHEATED_KERNEL
    await asyncio.sleep(NOTEBOOK_EXECUTION_TIME + 1)


async def test_env_variable_defined_in_kernel(http_server_client, base_url):
    await asyncio.sleep(NUMBER_PREHEATED_KERNEL * NOTEBOOK_EXECUTION_TIME + 1)
    _, text = await send_request(sc=http_server_client, url=base_url)
    assert "bar" in text
    await asyncio.sleep(NOTEBOOK_EXECUTION_TIME + 1)
