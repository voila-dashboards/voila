# simply tests if some notebooks execute
import pytest


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return [f'--VoilaTest.root_dir={notebook_directory!r}', '--VoilaTest.log_level=DEBUG'] + voila_args_extra


@pytest.mark.gen_test
def test_other_comms(http_client, base_url):
    response = yield http_client.fetch(f'{base_url}/voila/render/other_comms.ipynb')
    html_text = response.body.decode('utf-8')
    assert 'This notebook executed' in html_text
