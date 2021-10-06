import pytest
import time
import asyncio
import os

BASE_DIR = os.path.dirname(__file__)
NOTEBOOK_EXECUTION_TIME = 2
NUMBER_PREHEATED_KERNEL = 2
TIME_THRESHOLD = 1

@pytest.fixture
def voila_config_file_paths_arg():
    path = os.path.join(BASE_DIR, '..', 'configs', 'preheat')
    return '--VoilaTest.config_file_paths=[%r]' % path


@pytest.fixture
def preheat_mode():
    return True


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'preheat')


async def send_request(sc, url, wait=0):
    await asyncio.sleep(wait)
    real_time = time.time()
    response = await sc.fetch(url)
    real_time = time.time() - real_time
    html_text = response.body.decode("utf-8")
    return real_time, html_text


async def test_render_notebook_with_heated_kernel(http_server_client, base_url):
    await asyncio.sleep(NUMBER_PREHEATED_KERNEL*NOTEBOOK_EXECUTION_TIME + 1)
    time, text = await send_request(sc=http_server_client, url=f'{base_url}voila/render/pre_heat.ipynb')

    assert 'hello world' in text
    assert time < TIME_THRESHOLD


async def test_render_blacklisted_notebook_with_nornal_kernel(http_server_client, base_url):
    await asyncio.sleep(NUMBER_PREHEATED_KERNEL*NOTEBOOK_EXECUTION_TIME + 1)
    time, text = await send_request(sc=http_server_client, url=f'{base_url}voila/render/blacklisted.ipynb')

    assert 'hello world' in text
    assert time > TIME_THRESHOLD
