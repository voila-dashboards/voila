from fps.config import PluginModel, get_config  # type: ignore
from fps.hooks import register_config, register_plugin_name  # type: ignore


class VoilaConfig(PluginModel):
    notebook_path: str = ""


def get_voila_config():
    return get_config(VoilaConfig)


c = register_config(VoilaConfig)
n = register_plugin_name("Voila")
