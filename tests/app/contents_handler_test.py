import json
import pytest
import tornado


@pytest.fixture
def preheat_mode():
    return False


@pytest.fixture
def contents_prefix(base_url):
    return base_url + "voila/api/contents"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return [f"--VoilaTest.root_dir={notebook_directory!r}", *voila_args_extra]


@pytest.fixture
def voila_args_extra():
    return ['--VoilaConfiguration.extension_language_mapping={".py": "python"}']


async def test_contents_endpoint(http_server_client, contents_prefix):
    response = await http_server_client.fetch(contents_prefix)
    html_json = json.loads(response.body.decode("utf-8"))
    assert "content" in html_json
    assert len(html_json["content"]) > 0


async def test_get_notebook(http_server_client, contents_prefix):
    response = await http_server_client.fetch(contents_prefix + "/autokill.ipynb")
    html_json = json.loads(response.body.decode("utf-8"))
    assert html_json["name"] == "autokill.ipynb"
    assert html_json["content"] is None


async def test_get_not_allowed_file(http_server_client, contents_prefix):
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch(contents_prefix + "/print.xcpp")


async def test_get_allowed_file(http_server_client, contents_prefix):
    response = await http_server_client.fetch(contents_prefix + "/print.py")
    html_json = json.loads(response.body.decode("utf-8"))
    assert html_json["name"] == "print.py"
    assert html_json["content"] is None
