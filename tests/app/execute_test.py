# test basics of voila running a notebook
import tornado.web

import re
import json
import asyncio

try:
    from unittest import mock
except ImportError:
    import mock


async def test_hello_world(http_server_client, base_url, wait_for_kernel):
    await wait_for_kernel()
    response = await http_server_client.fetch(base_url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voilà' in html_text
    assert 'print(' not in html_text, 'by default the source code should be stripped'
    assert 'test_template.css' not in html_text, "test_template should not be the default"


async def test_no_execute_allowed(voila_app, app, http_server_client, base_url, http_server_port, wait_for_kernel):
    await wait_for_kernel()
    assert voila_app.app is app
    response = (await http_server_client.fetch(base_url)).body.decode('utf-8')
    pattern = r"""kernelId": ["']([0-9a-zA-Z-]+)["']"""
    groups = re.findall(pattern, response)
    kernel_id = groups[0]
    print(kernel_id, base_url)
    session_id = '445edd75-c6f5-45d2-8b58-5fe8f84a7123'
    url = f'ws://localhost:{http_server_port[1]}{base_url}api/kernels/{kernel_id}/channels?session_id={session_id}'
    conn = await tornado.websocket.websocket_connect(url)

    msg = {
        "header": {
            "msg_id": "8573fb401ac848aab63c3bf0081e9b65",
            "username": "username",
            "session": "7a7d94334ea745f888d9c479fa738d63",
            "msg_type": "execute_request",
            "version": "5.2",
        },
        "metadata": {},
        "content": {
            "code": "print('la')",
            "silent": False,
            "store_history": False,
            "user_expressions": {},
            "allow_stdin": False,
            "stop_on_error": False,
        },
        "buffers": [],
        "parent_header": {},
        "channel": "shell",
    }
    with mock.patch.object(voila_app.log, 'warning') as mock_warning:
        await conn.write_message(json.dumps(msg))
        # make sure the warning method is called
        while not mock_warning.called:
            await asyncio.sleep(0.1)
    mock_warning.assert_called_with('Received message of type "execute_request", which is not allowed. Ignoring.')
