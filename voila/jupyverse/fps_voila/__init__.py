from asphalt.core import run_application as _run_application

from .main import RootComponent


__version__ = "0.1.0"


def run_application(settings, voila_configuration, static_paths, base_url, ip, port):
    _run_application(
        RootComponent(
            settings,
            voila_configuration,
            static_paths,
            base_url,
            ip,
            port,
        )
    )
