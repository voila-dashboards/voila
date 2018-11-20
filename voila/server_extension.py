#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os
import gettext
from pathlib import Path
import tempfile
import json

import tornado.web
from jinja2 import Environment, FileSystemLoader

from jupyter_server.utils import url_path_join
from jupyter_server.base.handlers import path_regex
from jupyter_server.services.kernels.kernelmanager import MappingKernelManager
from jupyter_server.services.kernels.handlers import KernelHandler, ZMQChannelsHandler

from jupyter_client.jsonutil import date_default
from ipython_genutils.py3compat import cast_unicode

from .paths import ROOT, TEMPLATE_ROOT, STATIC_ROOT
from .handler import VoilaHandler
from .treehandler import VoilaTreeHandler
from .app import base_handlers
from .utils import add_base_url_to_handlers

from tornado import gen, web

def load_jupyter_server_extension(server_app):
    web_app = server_app.web_app

    jenv_opt = {"autoescape": True}
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_ROOT)), extensions=['jinja2.ext.i18n'], **jenv_opt)
    web_app.settings['voila_jinja2_env'] = env

    nbui = gettext.translation('nbui', localedir=str(ROOT / 'i18n'), fallback=True)
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
    handlers = [
        ('/voila/render' + path_regex, VoilaHandler),
        ('/voila', VoilaTreeHandler),
        ('/voila/tree' + path_regex, VoilaTreeHandler),
        ('/voila/static/(.*)',  tornado.web.StaticFileHandler, {'path': str(STATIC_ROOT)})
    ] + base_handlers
    print(add_base_url_to_handlers(base_url, base_handlers))
    web_app.add_handlers(host_pattern, add_base_url_to_handlers(base_url, handlers))
