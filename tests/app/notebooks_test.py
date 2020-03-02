# simply tests if some notebooks execute
import pytest


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--Voila.root_dir=%r' % notebook_directory, '--Voila.log_level=DEBUG'] + voila_args_extra


#@pytest.mark.gen_test
async def test_other_comms(http_client, add_token, base_url):
    url = add_token(base_url + '/voila/render/other_comms.ipynb')
    response = yield http_client.fetch(url)
    html_text = response.body.decode('utf-8')
    assert 'This notebook executed' in html_text
