import pytest
import json
import os


BASE_DIR = os.path.dirname(__file__)


@pytest.fixture
def voila_args_extra():
    return ['--VoilaConfiguration.strip_sources=False']


@pytest.mark.gen_test
def test_template_gridstack(http_client, base_url):
    response = yield http_client.fetch(base_url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voila' in html_text
    assert 'print' in html_text, 'the source code should *NOT* be stripped'
