import pytest
import tornado

from voila.static_file_handler import TemplateStaticFileHandler


async def test_static_file_absolute_path(app, base_url, http_server_client):
    response_lab = await http_server_client.fetch(f'{base_url}voila/templates/lab/static/voila.js')
    assert response_lab.code == 200
    abspath = TemplateStaticFileHandler.get_absolute_path(None, 'lab/static/voila.js')
    with open(abspath, encoding='utf-8', errors='replace') as f:
        content = f.read()
    assert response_lab.body.decode('utf-8') == content


async def test_static_file_not_found(app, base_url, http_server_client):
    with pytest.raises(tornado.httpclient.HTTPClientError, match='HTTP 404.*'):
        await http_server_client.fetch(f'{base_url}voila/templates/lab/static/doesnotexist.js')


async def test_static_file_availability_default(app, base_url, http_server_client):
    response_lab = await http_server_client.fetch(f'{base_url}voila/templates/lab/static/voila.js')
    response_default = await http_server_client.fetch(f'{base_url}voila/static/voila.js')
    assert response_lab.code == 200
    assert response_default.code == 200
    assert response_lab.body.decode('utf-8') == response_default.body.decode('utf-8')


async def test_static_file_override(app, base_url, http_server_client):
    response_lab = await http_server_client.fetch(f'{base_url}voila/templates/lab/static/voila.js')
    response_test_template = await http_server_client.fetch(f'{base_url}voila/templates/test_template/static/voila.js')
    assert response_lab.code == 200
    assert response_test_template.code == 200
    assert response_lab.body.decode('utf-8') != response_test_template.body.decode('utf-8')


async def test_static_file_other_template(app, base_url, http_server_client):
    response = await http_server_client.fetch(f'{base_url}voila/templates/test_template/static/only-in-test-template.js')
    assert response.code == 200
    assert response.body.decode('utf-8') == '', "empty file expected"
