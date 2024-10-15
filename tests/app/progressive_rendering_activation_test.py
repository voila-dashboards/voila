import os
import voila.app
import pytest


@pytest.fixture
def progressive_rendering_mode():
    return True


@pytest.fixture
def preheat_mode():
    return True


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, "preheat", "pre_heat.ipynb")


class VoilaTest(voila.app.Voila):
    def listen(self):
        pass


def test_voila(voila_args, voila_config, preheat_config, progressive_rendering_config):
    with pytest.raises(Exception) as e_info:
        voila_app = VoilaTest.instance()
        voila_app.initialize(
            [*voila_args, "--no-browser", preheat_config, progressive_rendering_config]
        )
        voila_config(voila_app)
        voila_app.start()
    assert (
        str(e_info.value)
        == "`preheat_kernel` and `progressive_rendering` are incompatible"
    )
