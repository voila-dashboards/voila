#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

from zmq.eventloop import ioloop

ioloop.install()

import os
import shutil
import tempfile
import json
import logging
import gettext

import jinja2
import nbconvert

import tornado.ioloop
import tornado.web

from traitlets.config.application import Application
from traitlets import Unicode, Integer, Bool, default

from jupyter_server.services.kernels.kernelmanager import MappingKernelManager
from jupyter_server.services.kernels.handlers import KernelHandler, ZMQChannelsHandler
from jupyter_server.base.handlers import path_regex
from jupyter_server.services.contents.largefilemanager import LargeFileManager
from jupyter_server.utils import url_path_join

from .paths import ROOT, STATIC_ROOT, TEMPLATE_ROOT
from .handler import VoilaHandler
from .treehandler import VoilaTreeHandler

_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"


class Voila(Application):
    name = 'voila'
    examples = 'voila example.ipynb --port 8888'
    description = Unicode(
        """voila [OPTIONS] NOTEBOOK_FILENAME

        This launches a stand-alone server for read-only notebooks.
        """
    )
    option_description = Unicode(
        """
        notebook_path:
            File name of the Jupyter notebook to display.
        """
    )
    notebook_filename = Unicode()
    strip_sources = Bool(True, help='Strip sources from rendered html').tag(config=True)
    port = Integer(
        8866,
        config=True,
        help='Port of the voila server. Default 8866.'
    )
    autoreload = Bool(
        False,
        config=True,
        help='Will autoreload to server and the page when a template, js file or Python code changes'
    )
    static_root = Unicode(
        str(STATIC_ROOT),
        config=True,
        help='Directory holding static assets (HTML, JS and CSS files).'
    )
    custom_path = Unicode(
        None,
        config=True,
        allow_none=True,
        help='Directory containing templates, js and css.'
    )
    aliases = {
        'port': 'Voila.port',
        'static': 'Voila.static_root',
        'strip_sources': 'Voila.strip_sources',
        'custom_path': 'Voila.custom_path',
        'autoreload': 'Voila.autoreload'
    }
    connection_dir_root = Unicode(
        config=True,
        help=(
            'Location of temporary connection files. Defaults '
            'to system `tempfile.gettempdir()` value.'
        )
    )
    connection_dir = Unicode()

    @default('connection_dir_root')
    def _default_connection_dir(self):
        return tempfile.gettempdir()
        connection_dir = tempfile.mkdtemp()
        self.log.info(f'Using {connection_dir} to store connection files')
        return connection_dir

    @default('log_level')
    def _default_log_level(self):
        return logging.INFO

    def parse_command_line(self, argv=None):
        super(Voila, self).parse_command_line(argv)
        self.notebook_path = self.extra_args[0] if len(self.extra_args) == 1 else None

    def start(self):
        connection_dir = tempfile.mkdtemp(
            prefix='voila_',
            dir=self.connection_dir_root
        )
        self.log.info(f'Storing connection files in {connection_dir}.')
        self.log.info(f'Serving static files from {self.static_root}.')

        kernel_manager = MappingKernelManager(
            connection_dir=connection_dir,
            allowed_message_types=[
                'comm_msg',
                'comm_info_request',
                'kernel_info_request',
                'custom_message',
                'shutdown_request'
            ]
        )

        jenv_opt = {"autoescape": True}  # we might want extra options via cmd line like notebook server
        nbpath = os.path.dirname(nbconvert.__file__)
        template_paths = [str(TEMPLATE_ROOT),
                          os.path.join(nbpath, 'templates'),
                          os.path.join(nbpath, 'templates/skeleton'),
                          os.path.join(nbpath, 'templates/html')]
        if self.custom_path:
            template_paths.insert(0, self.custom_path)
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_paths), extensions=['jinja2.ext.i18n'], **jenv_opt)
        nbui = gettext.translation('nbui', localedir=str(ROOT / 'i18n'), fallback=True)
        env.install_gettext_translations(nbui, newstyle=False)
        contents_manager = LargeFileManager()  # TODO: make this configurable like notebook

        webapp = tornado.web.Application(
            kernel_manager=kernel_manager,
            allow_remote_access=True,
            autoreload=self.autoreload,
            voila_jinja2_env=env,
            template_paths=template_paths,
            jinja2_env=env,
            static_path='/',
            server_root_dir='/',
            contents_manager=contents_manager
        )

        base_url = webapp.settings.get('base_url', '/')

        handlers = []

        handlers.extend([
            (url_path_join(base_url, r'/api/kernels/%s' % _kernel_id_regex), KernelHandler),
            (url_path_join(base_url, r'/api/kernels/%s/channels' % _kernel_id_regex), ZMQChannelsHandler),
            (
                url_path_join(base_url, r'/voila/static/(.*)'),
                tornado.web.StaticFileHandler,
                {
                    'path': self.static_root,
                    'default_filename': 'index.html'
                }
            )
        ])

        if self.custom_path:
            for sub in ['css', 'js', 'vendor']:
                handlers.append((
                        url_path_join(base_url, r'/voila/custom/{sub}/(.*)'.format(sub=sub)),
                        tornado.web.StaticFileHandler,
                        {
                            'path': os.path.join(self.custom_path, sub)
                        }
                    )
                )


        if self.notebook_path:
            handlers.append((
                url_path_join(base_url, r'/'),
                VoilaHandler,
                {
                    'notebook_path': self.notebook_path,
                    'strip_sources': self.strip_sources
                }
            ))
        else:
            handlers.extend([
                (base_url, VoilaTreeHandler),
                (url_path_join(base_url, r'/voila/tree' + path_regex), VoilaTreeHandler),
                (url_path_join(base_url, r'/voila/render' + path_regex), VoilaHandler, {'strip_sources': self.strip_sources}),
            ])

        webapp.add_handlers('.*$', handlers)

        webapp.listen(self.port)
        self.log.info(f'Voila listening on port {self.port}.')

        try:
            tornado.ioloop.IOLoop.current().start()
        finally:
            shutil.rmtree(connection_dir)

main = Voila.launch_instance

if __name__ == '__main__':
    main()
