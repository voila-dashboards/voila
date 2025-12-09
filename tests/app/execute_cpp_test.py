import os

import pytest

TEST_XEUS_CPP = os.environ.get("VOILA_TEST_XEUS_CPP", "") == "1"
NOTEBOOK_PATH = "print.xcpp"


@pytest.fixture
def cpp_file_url(base_url, preheat_mode):
    return base_url + f"voila/render/{NOTEBOOK_PATH}"


@pytest.fixture
def voila_args_extra():
    return [
        '--VoilaConfiguration.extension_language_mapping={".xcpp": "C++23"}',
        "--VoilaExecutor.timeout=240",
    ]


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra, preheat_mode):
    return ["--VoilaTest.root_dir=%r" % notebook_directory, *voila_args_extra]


@pytest.mark.skipif(
    not TEST_XEUS_CPP, reason="opt in to avoid having to install xeus-cpp"
)
async def test_non_existing_kernel(http_server_client, cpp_file_url):
    response = await http_server_client.fetch(cpp_file_url)
    assert response.code == 200
    assert "Hello Voilà, from c++" in response.body.decode("utf-8")
