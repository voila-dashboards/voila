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

from .tornado.contentshandler import VoilaContentsHandler

from .configuration import VoilaConfiguration
from .tornado.handler import TornadoVoilaHandler
from .paths import ROOT, collect_static_paths, collect_template_paths, jupyter_path
from .shutdown_kernel_handler import VoilaShutdownKernelHandler
from .static_file_handler import (
    MultiStaticFileHandler,
    TemplateStaticFileHandler,
    AllowListFileHandler,
)
from .tornado.treehandler import TornadoVoilaTreeHandler
from .utils import (
    get_data_dir,
    get_server_root_dir,
    pjoin,
    get_voila_labextensions_path,
)


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

    themes_dir = pjoin(get_data_dir(), "themes")
    labextensions_path = get_voila_labextensions_path()

    web_app.add_handlers(
        host_pattern,
        [
            (
                url_path_join(base_url, "/voila/render/(.*)"),
                TornadoVoilaHandler,
                {
                    "config": server_app.config,
                    "template_paths": template_paths,
                    "voila_configuration": voila_configuration,
                },
            ),
            (
                url_path_join(base_url, "/voila"),
                TornadoVoilaTreeHandler,
                tree_handler_conf,
            ),
            (
                url_path_join(base_url, "/voila/tree" + path_regex),
                TornadoVoilaTreeHandler,
                tree_handler_conf,
            ),
            (
                url_path_join(base_url, "/voila/templates/(.*)"),
                TemplateStaticFileHandler,
            ),
            (
                url_path_join(base_url, r"/voila/api/themes/(.*)"),
                ThemesHandler,
                {
                    "themes_url": "/voila/api/themes",
                    "path": themes_dir,
                    "labextensions_path": labextensions_path,
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
                AllowListFileHandler,
                {
                    "allowlist": voila_configuration.file_allowlist,
                    "denylist": voila_configuration.file_denylist,
                    "path": os.path.expanduser(get_server_root_dir(web_app.settings)),
                },
            ),
            (
                url_path_join(base_url, r"/voila/api/contents%s" % path_regex),
                VoilaContentsHandler,
                tree_handler_conf,
            ),
        ],
    )

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
