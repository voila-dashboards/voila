# simply tests if some notebooks execute
import sys

import pytest


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra):
    return ['--VoilaTest.root_dir=%r' % notebook_directory, '--VoilaTest.log_level=DEBUG'] + voila_args_extra


@pytest.mark.gen_test
@pytest.mark.skipif(sys.version_info < (3, 6), reason="Matplotlib installation issue on MacOS, Python 3.5")
def test_other_comms(http_client, base_url):
    response = yield http_client.fetch(base_url + '/voila/render/other_comms.ipynb')
    html_text = response.body.decode('utf-8')
    assert 'This notebook executed' in html_text
