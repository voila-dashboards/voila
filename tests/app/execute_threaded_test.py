# test basics of voila running a notebook
import pytest


@pytest.fixture 
def voila_args_extra():
    return ['--VoilaExporter.cell_executor_class=voila.execute_threaded.CellExecutorThreaded']


@pytest.mark.gen_test
def test_hello_world(app, http_client, base_url):
    response = yield http_client.fetch(base_url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voila' in html_text
    assert 'print' not in html_text, 'by default the source code should be stripped'
    assert 'test_template.css' not in html_text, "test_template should not be the default"
