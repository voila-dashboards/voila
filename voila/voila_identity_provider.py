from typing import Any, Optional
from jupyter_server.auth.identity import IdentityProvider
from jupyter_server.auth.login import LoginFormHandler


class VoilaLoginHandler(LoginFormHandler):
    def static_url(
        self, path: str, include_host: Optional[bool] = None, **kwargs: Any
    ) -> str:
        settings = {
            "static_url_prefix": "voila/static/",
            "static_path": None,
        }
        return settings.get("static_url_prefix", "/static/") + path


class VoilaIdentityProvider(IdentityProvider):
    @property
    def auth_enabled(self) -> bool:
        """Return whether any auth is enabled"""
        return bool(self.token)
