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
import tempfile

from jinja2 import Environment, FileSystemLoader

from jupyter_server.utils import url_path_join
from jupyter_server.base.handlers import path_regex, FileFindHandler
from jupyter_server.services.kernels.kernelmanager import MappingKernelManager

from .paths import ROOT, collect_template_paths, collect_static_paths, jupyter_path
from .handler import VoilaHandler
from .treehandler import VoilaTreeHandler
from .static_file_handler import MultiStaticFileHandler, WhiteListFileHandler
from .configuration import VoilaConfiguration
from .utils import add_base_url_to_handlers, get_server_root_dir
from .app import base_handlers


def _jupyter_server_extension_paths():
    """
    Returns a list of dictionaries with metadata describing
    where to find the `_load_jupyter_server_extension` function.
    """
    return [
        {
            "module": "voila.server_extension"
        }
    ]


def _load_jupyter_server_extension(server_app):
    web_app = server_app.web_app

    # common configuration options between the server extension and the application
    voila_configuration = VoilaConfiguration(parent=server_app)
    template_name = voila_configuration.template
    template_paths = collect_template_paths(['voila', 'nbconvert'], template_name)
    static_paths = collect_static_paths(['voila', 'nbconvert'], template_name)

    jenv_opt = {"autoescape": True}
    env = Environment(loader=FileSystemLoader(template_paths), extensions=['jinja2.ext.i18n'], **jenv_opt)
    web_app.settings['voila_jinja2_env'] = env

    nbui = gettext.translation('nbui', localedir=os.path.join(ROOT, 'i18n'), fallback=True)
    env.install_gettext_translations(nbui, newstyle=False)

    connection_dir = tempfile.gettempdir()

    kernel_mapping_manager = MappingKernelManager(
        connection_dir=connection_dir,
        allowed_message_types=[
            'comm_msg',
            'comm_info_request',
            'kernel_info_request',
            'custom_message',
            'shutdown_request'
        ]
    )
    web_app.settings['voila_kernel_manager'] = kernel_mapping_manager

    host_pattern = '.*$'
    base_url = url_path_join(web_app.settings['base_url'])

    tree_handler_conf = {
        'voila_configuration': voila_configuration
    }

    handlers =  [
        (r'/voila/render/(.*)', VoilaHandler, {
            'config': server_app.config,
            'template_paths': template_paths,
            'voila_configuration': voila_configuration
        }),
        (r'/voila', VoilaTreeHandler, tree_handler_conf),
        (r'/voila/tree' + path_regex, VoilaTreeHandler, tree_handler_conf),
        (r'/voila/static/(.*)', MultiStaticFileHandler, {'paths': static_paths}),
        (
            r'/voila/files/(.*)',
            WhiteListFileHandler,
            {
                'whitelist': voila_configuration.file_whitelist,
                'blacklist': voila_configuration.file_blacklist,
                'path': os.path.expanduser(get_server_root_dir(web_app.settings)),
            },
        ),
    ]

    # Serving notebook extensions
    if voila_configuration.enable_nbextensions:
        # First look into 'nbextensions_path' configuration key (classic notebook)
        # and fall back to default path for nbextensions (jupyter server).
        if 'nbextensions_path' in web_app.settings:
            nbextensions_path = web_app.settings['nbextensions_path']
        else:
            nbextensions_path = jupyter_path('nbextensions')

        handlers.extend([
            # this handler serves the nbextensions similar to the classical notebook
            (
                r'/voila/nbextensions/(.*)',
                FileFindHandler,
                {
                    'path': nbextensions_path,
                    'no_cache_paths': ['/'],  # don't cache anything in nbextensions
                },
            )
        ])

    handlers += base_handlers
    web_app.add_handlers(host_pattern, add_base_url_to_handlers(base_url, handlers))


# For backward compatibility
load_jupyter_server_extension = _load_jupyter_server_extension
