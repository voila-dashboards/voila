import pytest
import time
import asyncio
import os


@pytest.fixture
def preheat_mode():
    return True


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'pre_heat.ipynb')


NOTEBOOK_EXECUTION_TIME = 2


async def send_request(sc, url, wait=0):
    await asyncio.sleep(wait)
    real_time = time.time()
    response = await sc.fetch(url)
    real_time = time.time() - real_time
    html_text = response.body.decode('utf-8')
    return real_time, html_text


async def test_request_before_kernel_heated(http_server_client, base_url):
    """
    We send a request to server immediately, a normal kernel
    will be used so it should take more than `NOTEBOOK_EXECUTION_TIME`
    to display result.
    """
    time, text = await send_request(sc=http_server_client, url=base_url)
    assert 'hello world' in text
    assert time > NOTEBOOK_EXECUTION_TIME


async def test_render_time_with_preheated_kernel(http_server_client, base_url):
    """
    We wait for kernel properly heated before sending request,
    it should take under 0.5s to return result
    """
    time, text = await send_request(sc=http_server_client,
                                    url=base_url,
                                    wait=NOTEBOOK_EXECUTION_TIME + 2)
    assert 'hello world' in text
    assert time < 0.5


async def test_render_time_with_multiple_requests(http_server_client,
                                                  base_url):
    """
    We send a second request just after the first one, so the
    pool is not filled yet and a normal kernel is used instead
    """
    time_list = []
    for wait in [NOTEBOOK_EXECUTION_TIME + 1, 0]:

        time, _ = await send_request(sc=http_server_client,
                                     url=base_url,
                                     wait=wait)
        time_list.append(time)

    assert max(time_list) > 0.5  # Render time for a normal kernel
    assert min(time_list) < 0.5  # Render time for a preheated kernel


async def test_request_with_query(http_server_client, base_url):
    """
    We sent request with query parameter, preheat kernel should
    be disable is this case.
    """
    url = f'{base_url}?foo=bar'
    time, _ = await send_request(sc=http_server_client,
                                 url=url,
                                 wait=NOTEBOOK_EXECUTION_TIME + 1)
    assert time > 0.5


async def test_request_with_theme_parameter(http_server_client, base_url):
    """
    We sent request with theme parameter, preheat kernel should
    be used if requested theme is same as theme used for prerendered.
    """
    wait = NOTEBOOK_EXECUTION_TIME + 1

    url = f'{base_url}?voila-theme=light'
    time, _ = await send_request(sc=http_server_client, url=url, wait=wait)
    assert time < 0.5

    url = f'{base_url}?voila-theme=dark'
    time, _ = await send_request(sc=http_server_client, url=url, wait=wait)
    assert time > 0.5


async def test_request_with_template_parameter(http_server_client, base_url):
    """
    We sent request with theme parameter, preheat kernel should
    be used if requested theme is same as theme used for prerendered.
    """
    wait = NOTEBOOK_EXECUTION_TIME + 1

    url = f'{base_url}?voila-template=lab'
    time, _ = await send_request(sc=http_server_client, url=url, wait=wait)
    assert time < 0.5
