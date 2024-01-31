import json
import os

try:
    from jupyter_client.jsonutil import json_default
except ImportError:
    from jupyter_client.jsonutil import date_default as json_default
from tornado import web
from jupyter_server.base.handlers import APIHandler
from jupyter_server.services.contents.handlers import validate_model
from jupyter_core.utils import ensure_async


class VoilaContentsHandler(APIHandler):
    """Handle content requests from the tree page."""

    def initialize(self, **kwargs):
        super().initialize()
        voila_configuration = kwargs["voila_configuration"]
        self.allowed_extensions = [
            *list(voila_configuration.extension_language_mapping.keys()),
            ".ipynb",
        ]

    @web.authenticated
    async def get(self, path=""):
        """Return a model for a file or directory.

        A directory model contains a list of models (without content)
        of the files and directories it contains.
        """
        path = path or ""
        cm = self.contents_manager

        format = self.get_query_argument("format", default=None)
        if format not in {None, "text", "base64"}:
            raise web.HTTPError(400, "Format %r is invalid" % format)
        content_str = self.get_query_argument("content", default="1")
        if content_str not in {"0", "1"}:
            raise web.HTTPError(400, "Content %r is invalid" % content_str)
        content = int(content_str or "")

        if not cm.allow_hidden and await ensure_async(cm.is_hidden(path)):
            raise web.HTTPError(404, f"file or directory {path!r} does not exist")

        model = await ensure_async(
            self.contents_manager.get(
                path=path,
                type=None,
                format=format,
                content=content,
            )
        )

        validate_model(model, expect_content=content)

        def allowed_content(content):
            if content["type"] in ["directory", "notebook"]:
                return True
            __, ext = os.path.splitext(content.get("path"))
            return ext in self.allowed_extensions

        if not allowed_content(model):
            raise web.HTTPError(404, f"file or directory {path!r} does not exist")

        if model["type"] == "directory":
            try:
                model["content"] = sorted(model["content"], key=lambda i: i["name"])
                model["content"] = list(filter(allowed_content, model["content"]))
            except Exception:
                model["content"] = None
        else:
            # Make sure we don't leak the file content.
            model["content"] = None

        self._finish_model(model, location=False)

    def _finish_model(self, model, location=True):
        """Finish a JSON request with a model, setting relevant headers, etc."""
        if location:
            location = self.location_url(model["path"])
            self.set_header("Location", location)
        self.set_header("Last-Modified", model["last_modified"])
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps(model, default=json_default))
