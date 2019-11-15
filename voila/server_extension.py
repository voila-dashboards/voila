#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os
import gettext

from jinja2 import Environment, FileSystemLoader

from jupyter_server.utils import url_path_join
from jupyter_server.base.handlers import path_regex
from jupyter_server.base.handlers import FileFindHandler

from .paths import ROOT, STATIC_ROOT, collect_template_paths, jupyter_path
from .handler import VoilaHandler
from .treehandler import VoilaTreeHandler
from .static_file_handler import MultiStaticFileHandler, WhiteListFileHandler
from .configuration import VoilaConfiguration
from .utils import get_server_root_dir


def load_jupyter_server_extension(server_app):
    web_app = server_app.web_app

    nbconvert_template_paths = []
    static_paths = [STATIC_ROOT]
    template_paths = []

    # common configuration options between the server extension and the application
    voila_configuration = VoilaConfiguration(parent=server_app)
    collect_template_paths(
        nbconvert_template_paths,
        static_paths,
        template_paths,
        voila_configuration.template
    )

    jenv_opt = {"autoescape": True}
    env = Environment(loader=FileSystemLoader(template_paths), extensions=['jinja2.ext.i18n'], **jenv_opt)
    web_app.settings['voila_jinja2_env'] = env

    nbui = gettext.translation('nbui', localedir=os.path.join(ROOT, 'i18n'), fallback=True)
    env.install_gettext_translations(nbui, newstyle=False)

    host_pattern = '.*$'
    base_url = url_path_join(web_app.settings['base_url'])

    tree_handler_conf = {
        'voila_configuration': voila_configuration
    }
    web_app.add_handlers(host_pattern, [
        (url_path_join(base_url, '/voila/render/(.*)'), VoilaHandler, {
            'config': server_app.config,
            'nbconvert_template_paths': nbconvert_template_paths,
            'voila_configuration': voila_configuration
        }),
        (url_path_join(base_url, '/voila'), VoilaTreeHandler, tree_handler_conf),
        (url_path_join(base_url, '/voila/tree' + path_regex), VoilaTreeHandler, tree_handler_conf),
        (url_path_join(base_url, '/voila/static/(.*)'), MultiStaticFileHandler, {'paths': static_paths}),
        (
            url_path_join(base_url, r'/voila/files/(.*)'),
            WhiteListFileHandler,
            {
                'whitelist': voila_configuration.file_whitelist,
                'blacklist': voila_configuration.file_blacklist,
                'path': os.path.expanduser(get_server_root_dir(web_app.settings)),
            },
        ),
    ])

    # Serving notebook extensions
    if voila_configuration.enable_nbextensions:
        # First look into 'nbextensions_path' configuration key (classic notebook)
        # and fall back to default path for nbextensions (jupyter server).
        if 'nbextensions_path' in web_app.settings:
            nbextensions_path = web_app.settings['nbextensions_path']
        else:
            nbextensions_path = jupyter_path('nbextensions')

        web_app.add_handlers(host_pattern, [
            # this handler serves the nbextensions similar to the classical notebook
            (
                url_path_join(base_url, r'/voila/nbextensions/(.*)'),
                FileFindHandler,
                {
                    'path': nbextensions_path,
                    'no_cache_paths': ['/'],  # don't cache anything in nbextensions
                },
            )
        ])
