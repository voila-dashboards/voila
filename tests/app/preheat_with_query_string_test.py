import asyncio
import os
import time

import pytest


@pytest.fixture(params=[['--Voila.base_url="/base/"'], []])
def using_base_url(request):
    return request.param


@pytest.fixture(params=[['--Voila.server_url="/server/"'], []])
def using_server_url(request):
    return request.param


@pytest.fixture()
def voila_args_extra(http_server_port, using_server_url, using_base_url):
    return [f"--port={http_server_port[-1]}", *using_server_url, *using_base_url]


@pytest.fixture
def preheat_mode():
    return True


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, "preheat", "get_query_string.ipynb")


NOTEBOOK_EXECUTION_TIME = 2
TIME_THRESHOLD = NOTEBOOK_EXECUTION_TIME


async def send_request(sc, url, wait=0):
    await asyncio.sleep(wait)
    real_time = time.time()
    response = await sc.fetch(url)
    real_time = time.time() - real_time
    html_text = response.body.decode("utf-8")
    return real_time, html_text


async def test_request_with_query(
    http_server_client, base_url, using_base_url, using_server_url
):
    """
    We sent request with query parameter, `get_query_string` should
    return value.
    """
    if len(using_server_url) > 0:
        url = "/server/?foo=bar"
    else:
        if len(using_base_url) > 0:
            url = "/base/?foo=bar"
        else:
            url = f"{base_url}?foo=bar"
    _, html_text = await send_request(
        sc=http_server_client, url=url, wait=NOTEBOOK_EXECUTION_TIME + 1
    )
    assert "foo=bar" in html_text
