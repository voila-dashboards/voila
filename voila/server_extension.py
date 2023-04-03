#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import gettext
import os

from jinja2 import Environment, FileSystemLoader
from jupyter_server.base.handlers import FileFindHandler, path_regex
from jupyter_server.utils import url_path_join
from jupyterlab_server.themes_handler import ThemesHandler

from .configuration import VoilaConfiguration
from .handler import VoilaHandler
from .paths import ROOT, collect_static_paths, collect_template_paths, jupyter_path
from .shutdown_kernel_handler import VoilaShutdownKernelHandler
from .static_file_handler import (
    MultiStaticFileHandler,
    TemplateStaticFileHandler,
    WhiteListFileHandler,
)
from .treehandler import VoilaTreeHandler
from .utils import get_server_root_dir


def _jupyter_server_extension_points():
    """
    Returns a list of dictionaries with metadata describing
    where to find the `_load_jupyter_server_extension` function.
    """
    return [{"module": "voila.server_extension"}]


def _load_jupyter_server_extension(server_app):
    web_app = server_app.web_app
    # common configuration options between the server extension and the application
    voila_configuration = VoilaConfiguration(parent=server_app)
    template_name = voila_configuration.template
    template_paths = collect_template_paths(["voila", "nbconvert"], template_name)
    static_paths = collect_static_paths(["voila", "nbconvert"], template_name)

    jenv_opt = {"autoescape": True}
    env = Environment(
        loader=FileSystemLoader(template_paths),
        extensions=["jinja2.ext.i18n"],
        **jenv_opt,
    )
    web_app.settings["voila_jinja2_env"] = env

    nbui = gettext.translation(
        "nbui", localedir=os.path.join(ROOT, "i18n"), fallback=True
    )
    env.install_gettext_translations(nbui, newstyle=False)

    host_pattern = ".*$"
    base_url = url_path_join(web_app.settings["base_url"])

    tree_handler_conf = {"voila_configuration": voila_configuration}
    web_app.add_handlers(
        host_pattern,
        [
            (
                url_path_join(base_url, "/voila/render/(.*)"),
                VoilaHandler,
                {
                    "config": server_app.config,
                    "template_paths": template_paths,
                    "voila_configuration": voila_configuration,
                },
            ),
            (url_path_join(base_url, "/voila"), VoilaTreeHandler, tree_handler_conf),
            (
                url_path_join(base_url, "/voila/tree" + path_regex),
                VoilaTreeHandler,
                tree_handler_conf,
            ),
            (
                url_path_join(base_url, "/voila/templates/(.*)"),
                TemplateStaticFileHandler,
            ),
            (
                url_path_join(base_url, r"/voila/themes/(.*)"),
                ThemesHandler,
                {
                    "themes_url": "/voila/themes",
                    "path": "",
                    "labextensions_path": jupyter_path("labextensions"),
                    "no_cache_paths": ["/"],
                },
            ),
            (
                url_path_join(base_url, "/voila/static/(.*)"),
                MultiStaticFileHandler,
                {"paths": static_paths},
            ),
            (
                url_path_join(base_url, r"/voila/api/shutdown/(.*)"),
                VoilaShutdownKernelHandler,
            ),
            (
                url_path_join(base_url, r"/voila/files/(.*)"),
                WhiteListFileHandler,
                {
                    "whitelist": voila_configuration.file_whitelist,
                    "blacklist": voila_configuration.file_blacklist,
                    "path": os.path.expanduser(get_server_root_dir(web_app.settings)),
                },
            ),
        ],
    )

    # Serving lab extensions
    # TODO: reuse existing lab server endpoint?
    # First look into 'labextensions_path' configuration key (classic notebook)
    # and fall back to default path for labextensions (jupyter server).
    if "labextensions_path" in web_app.settings:
        labextensions_path = web_app.settings["labextensions_path"]
    else:
        labextensions_path = jupyter_path("labextensions")

    web_app.add_handlers(
        host_pattern,
        [
            (
                # TODO: update handler
                url_path_join(base_url, r"/voila/labextensions/(.*)"),
                FileFindHandler,
                {
                    "path": labextensions_path,
                    "no_cache_paths": ["/"],  # don't cache anything
                },
            )
        ],
    )


# For backward compatibility
load_jupyter_server_extension = _load_jupyter_server_extension
