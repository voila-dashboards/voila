#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################
from jupyter_server.utils import url_escape, url_path_join

from .handler import BaseVoilaHandler


class VoilaTreeHandler(BaseVoilaHandler):
    def initialize(self, **kwargs):
        super().initialize(**kwargs)
        self.allowed_extensions = [
            *list(self.voila_configuration.extension_language_mapping.keys()),
            ".ipynb",
        ]

    def validate_theme(self, theme: str, classic_tree: bool) -> str:
        """Check the compatibility between the requested theme and the tree page"""
        if classic_tree:
            supported_themes = ["dark", "light", "JupyterLab Dark", "JupyterLab Light"]
            if theme not in supported_themes:
                self.log.warn(
                    "Custom JupyterLab theme is not supported in the classic tree, failback to the light theme!"
                )
                return "light"
            else:
                if theme == "JupyterLab Dark":
                    return "dark"
                if theme == "JupyterLab Light":
                    return "light"
        return theme

    def get_template(self, name):
        """Return the jinja template object for a given name"""
        return self.settings["voila_jinja2_env"].get_template(name)

    def generate_breadcrumbs(self, path):
        breadcrumbs = [(url_path_join(self.base_url, "voila/tree"), "")]
        parts = path.split("/")
        for i in range(len(parts)):
            if parts[i]:
                link = url_path_join(
                    self.base_url,
                    "voila/tree",
                    url_escape(url_path_join(*parts[: i + 1])),
                )
                breadcrumbs.append((link, parts[i]))
        return breadcrumbs

    def generate_page_title(self, path):
        parts = path.split("/")
        if len(parts) > 3:  # not too many parts
            parts = parts[-2:]
        page_title = url_path_join(*parts)
        if page_title:
            return page_title + "/"
        else:
            return "Voilà Home"
