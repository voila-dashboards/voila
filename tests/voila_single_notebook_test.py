import pytest
import tornado.web
import tornado.gen
import voila.app
import os
import re
import json
import logging
from traitlets.config import Application
try:
    from unittest import mock
except:
    import mock

BASE_DIR = os.path.dirname(__file__)

class VoilaTest(voila.app.Voila):
    def listen(self):
        pass  # the ioloop is taken care of by the pytest-tornado framework

@pytest.fixture
def voila_app():
    voila_app = VoilaTest.instance()
    voila_app.initialize([os.path.join(BASE_DIR, 'notebooks/print.ipynb'), '--VoilaApp.log_level=DEBUG'])
    voila_app.start()
    return voila_app

@pytest.fixture
def app(voila_app):
    return voila_app.app

@pytest.mark.gen_test
def test_hello_world(http_client, base_url):
    response = yield http_client.fetch(base_url)
    assert response.code == 200
    assert 'Hi Voila' in response.body.decode('utf-8')

@pytest.mark.gen_test
def test_no_execute_allowed(voila_app, app, http_client, base_url):
    assert voila_app.app is app
    response = (yield http_client.fetch(base_url)).body.decode('utf-8')
    pattern  = r"""kernelId": ["']([0-9a-zA-Z-]+)["']"""
    groups = re.findall(pattern, response)
    kernel_id = groups[0]
    print(kernel_id, base_url)
    session_id = '445edd75-c6f5-45d2-8b58-5fe8f84a7123'
    url = '{base_url}/api/kernels/{kernel_id}/channels?session_id={session_id}'.format(
        kernel_id=kernel_id, base_url=base_url, session_id=session_id
    ).replace('http://', 'ws://')
    conn = yield tornado.websocket.websocket_connect(url)

    msg = {
        "header": {"msg_id":"8573fb401ac848aab63c3bf0081e9b65","username":"username","session":"7a7d94334ea745f888d9c479fa738d63","msg_type":"execute_request","version":"5.2"},
        "metadata":{},
        "content":{"code":"print('la')","silent":False,"store_history":False,"user_expressions":{},"allow_stdin":False,"stop_on_error":False},
        "buffers":[],
        "parent_header":{},
        "channel":"shell"
    }
    with mock.patch.object(voila_app.log, 'warning') as mock_warning:
        yield conn.write_message(json.dumps(msg))
        # make sure the warning method is called
        while not mock_warning.called:
            yield tornado.gen.sleep(0.1)
    mock_warning.assert_called_with('Received message of type "execute_request", which is not allowed. Ignoring.')
