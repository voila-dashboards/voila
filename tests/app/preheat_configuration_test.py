import pytest
import time
import asyncio
import os

BASE_DIR = os.path.dirname(__file__)

@pytest.fixture
def voila_config_file_paths_arg():
    path = os.path.join(BASE_DIR, '..', 'configs', 'preheat')
    return '--VoilaTest.config_file_paths=[%r]' % path


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra, voila_config_file_paths_arg):
    return [
        f"{notebook_directory}/pre_heat.ipynb",
        "--VoilaTest.log_level=INFO", voila_config_file_paths_arg
    ] + voila_args_extra 


NOTEBOOK_EXECUTION_TIME = 2
NUMBER_PREHEATED_KERNEL = 2

async def send_request(sc, url, wait=0):
    await asyncio.sleep(wait)
    real_time = time.time()
    response = await sc.fetch(url)
    real_time = time.time() - real_time
    html_text = response.body.decode("utf-8")
    return real_time, html_text


async def test_refill_kernel_asynchronously(http_server_client, base_url):
    await asyncio.sleep(NUMBER_PREHEATED_KERNEL*NOTEBOOK_EXECUTION_TIME + 1)
    fast = []
    slow = []
    for i in range(5*NUMBER_PREHEATED_KERNEL):
        time, _ = await send_request(sc=http_server_client, url=base_url)
        if time < 0.5:
            fast.append(time)
        else:
            slow.append(time)
    
    assert len(fast) == 7
    assert len(slow) == 3


async def test_env_variable_defined_in_kernel(http_server_client, base_url):
    await asyncio.sleep(NUMBER_PREHEATED_KERNEL*NOTEBOOK_EXECUTION_TIME + 1)
    _, text = await send_request(sc=http_server_client, url=base_url)
    assert "bar" in text

