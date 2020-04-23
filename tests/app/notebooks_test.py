# simply tests if some notebooks execute
import pytest


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--VoilaTest.root_dir=%r' % notebook_directory, '--VoilaTest.log_level=DEBUG'] + voila_args_extra


async def test_other_comms(http_server_client, base_url):
    response = await http_server_client.fetch(base_url + '/voila/render/other_comms.ipynb')
    html_text = response.body.decode('utf-8')
    assert 'This notebook executed' in html_text
