from zmq.eventloop import ioloop

ioloop.install()

import os
import shutil
import tempfile
import json
import logging

import tornado.ioloop
import tornado.web

from pathlib import Path

from traitlets.config.application import Application
from traitlets import Unicode, Integer, Bool, default

from jupyter_server.utils import url_path_join, url_escape
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.services.kernels.kernelmanager import MappingKernelManager
from jupyter_server.services.kernels.handlers import KernelHandler, MainKernelHandler, ZMQChannelsHandler

from jupyter_client.jsonutil import date_default

import nbformat
from nbconvert.preprocessors.execute import executenb
from nbconvert import HTMLExporter

ROOT = Path(os.path.dirname(__file__))
DEFAULT_STATIC_ROOT = ROOT / 'static'
TEMPLATE_ROOT = ROOT / 'templates'


class VoilaKernelHandler(JupyterHandler):

    def initialize(self, notebook=None, strip_sources=False):
        self.notebook = notebook
        self.strip_sources = strip_sources

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def get(self):

        # Ignore requested kernel name and make use of the one specified in the notebook.
        kernel_name = self.notebook.metadata.get('kernelspec', {}).get('name', self.kernel_manager.default_kernel_name)

        # Launch kernel and execute notebook.
        kernel_id = yield tornado.gen.maybe_future(self.kernel_manager.start_kernel(kernel_name=kernel_name))
        km = self.kernel_manager.get_kernel(kernel_id)
        result = executenb(self.notebook, km=km)

        # render notebook to html
        resources = dict(kernel_id=kernel_id)
        html, resources = HTMLExporter(template_file=str(TEMPLATE_ROOT / 'voila.tpl'), exclude_input=self.strip_sources,
                                       exclude_output_prompt=self.strip_sources, exclude_input_prompt=self.strip_sources
                                      ).from_notebook_node(result, resources=resources)

        # Compose reply
        self.set_header('Content-Type', 'text/html')
        self.write(html)

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
        notebook_filename:
            File name of the Jupyter notebook to display.
        """
    )
    notebook_filename = Unicode()
    strip_sources = Bool().tag(config=True)
    port = Integer(
        8866,
        config=True,
        help='Port of the voila server. Default 8866.'
    )
    static_root = Unicode(
        str(DEFAULT_STATIC_ROOT),
        config=True,
        help='Directory holding static assets (HTML, JS and CSS files).'
    )
    aliases = {
        'port': 'Voila.port',
        'static': 'Voila.static_root'
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
        try:
            notebook_filename = self.extra_args[0]
        except IndexError:
            self.log.critical('Bad command line parameters.')
            self.log.critical('Missing NOTEBOOK_FILENAME parameter.')
            self.log.critical('Run `voila --help` for help on command line parameters.')
            exit(1)
        self.notebook_filename = notebook_filename

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
                'comm_info_request',
                'kernel_info_request',
                'custom_message',
                'shutdown_request'
            ]
        )

        notebook = nbformat.read(self.notebook_filename, as_version=4)

        handlers = [
            (
                r'/',
                VoilaKernelHandler,
                {
                    'notebook': notebook,
                    'strip_sources': self.strip_sources
                }
            ),
            (r'/api/kernels/%s' % _kernel_id_regex, KernelHandler),
            (r'/api/kernels/%s/channels' % _kernel_id_regex, ZMQChannelsHandler),
            (
                r"/(.*)",
                tornado.web.StaticFileHandler,
                {
                    'path': self.static_root,
                    'default_filename': 'index.html'
                }
            )
        ]

        app = tornado.web.Application(
            handlers,
            kernel_manager=kernel_manager,
            allow_remote_access=True
        )

        app.listen(self.port)
        self.log.info(f'Voila listening on port {self.port}.')

        try:
            tornado.ioloop.IOLoop.current().start()
        finally:
            shutil.rmtree(connection_dir)

main = Voila.launch_instance

if __name__ == '__main__':
    main()
