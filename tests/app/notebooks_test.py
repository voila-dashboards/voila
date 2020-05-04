# simply tests if some notebooks execute
import pytest


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--Voila.root_dir=%r' % notebook_directory, '--Voila.log_level=DEBUG'] + voila_args_extra + ['--no-browser']


async def test_other_comms(fetch):
    response = await fetch('voila', 'render', 'other_comms.ipynb', method='GET')
    html_text = response.body.decode('utf-8')
    assert 'This notebook executed' in html_text
