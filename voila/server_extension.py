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
from .app import _kernel_id_regex

from tornado import gen, web

class VoilaNotebookKernelManager(KernelHandler):
    @property
    def kernel_manager(self):
        return self.settings['voila_kernel_manager']

    # @web.authenticated
    def get(self, kernel_id):
        km = self.kernel_manager
        km._check_kernel_id(kernel_id)
        model = km.kernel_model(kernel_id)
        self.finish(json.dumps(model, default=date_default))

    # @web.authenticated
    @gen.coroutine
    def delete(self, kernel_id):
        km = self.kernel_manager
        yield gen.maybe_future(km.shutdown_kernel(kernel_id))
        self.set_status(204)
        self.finish()

class VoilaNotebookZMQChannelsHandler(ZMQChannelsHandler):
    def get_current_user(self):
        return "voila"  # bypass AuthenticatedZMQStreamHandler's security handling

    @property
    def kernel_manager(self):
        return self.settings['voila_kernel_manager']

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
    web_app.add_handlers(host_pattern, [
        (url_path_join(base_url, '/voila/render' + path_regex), VoilaHandler),
        (url_path_join(base_url, '/voila'), VoilaTreeHandler),
        (url_path_join(base_url, '/voila/tree' + path_regex), VoilaTreeHandler),
        (url_path_join(base_url, '/voila/static/(.*)'),  tornado.web.StaticFileHandler, {'path': str(STATIC_ROOT)})
    ])

    web_app.add_handlers(host_pattern, [
        (url_path_join(base_url, r'/voila/api/kernels/%s' % _kernel_id_regex), VoilaNotebookKernelManager),
        (url_path_join(base_url, r'/voila/api/kernels/%s/channels' % _kernel_id_regex), VoilaNotebookZMQChannelsHandler),
    ])
