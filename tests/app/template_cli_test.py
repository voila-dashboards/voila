# tests programmatic config of template sytem
import pytest

import os

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_args_extra():
    path_test_template = os.path.abspath(os.path.join(BASE_DIR, '../test_template/share/jupyter/voila/templates/test_template/'))
    path_default = os.path.abspath(os.path.join(BASE_DIR, '../../share/jupyter/voila/templates/default'))
    return ['--template=None', '--VoilaTest.template_paths=[%r, %r]' % (path_test_template, path_default), '--VoilaExecutor.timeout=240']


async def test_template_test(http_server_client, base_url):
    response = await http_server_client.fetch(base_url)
    assert response.code == 200
    assert 'test_template.css' in response.body.decode('utf-8')
