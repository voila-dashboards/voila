# test serving a notebook
import pytest


@pytest.fixture
def cwd_subdir_notebook_url(base_url):
    return base_url + "/voila/render/subdir/cwd_subdir.ipynb"


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return [
        "--ServerApp.root_dir=%r" % notebook_directory,
        "--Voila.log_level=DEBUG",
    ] + voila_args_extra


@pytest.mark.gen_test
def test_hello_world(http_client, add_token, cwd_subdir_notebook_url):
    url = add_token(cwd_subdir_notebook_url)
    response = yield http_client.fetch(url)
    html_text = response.body.decode("utf-8")
    assert "check for the cwd" in html_text
