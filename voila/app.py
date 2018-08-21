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

from tornado.web import RequestHandler

from jupyter_server.utils import url_path_join, url_escape
from jupyter_server.services.kernels.kernelmanager import MappingKernelManager
from jupyter_server.services.kernels.handlers import KernelHandler, MainKernelHandler, ZMQChannelsHandler

from jupyter_client.jsonutil import date_default

import nbformat
from nbconvert.preprocessors.execute import executenb
from nbconvert import HTMLExporter

ROOT = Path(os.path.dirname(__file__))
DEFAULT_STATIC_ROOT = ROOT / 'static'


class VoilaKernelHandler(MainKernelHandler):

    def initialize(self, notebook=None, strip_sources=False):
        self.notebook = notebook
        self.strip_sources = True

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def get(self):
        km = self.kernel_manager

        # Ignore requested kernel name and make use of the one specified in the notebook.
        kernel_name = self.notebook.metadata.get('kernelspec', {}).get('name', km.default_kernel_name)

        # Launch kernel and execute notebook.
        kernel_id = yield tornado.gen.maybe_future(km.start_kernel(kernel_name=kernel_name))
        result = executenb(self.notebook, km=km)

        # Optionally, delete source of code cells.
        # TODO: make use of global_content_filters instead
        if self.strip_sources:
            for cell in result.cells:
                if cell.cell_type == 'code':
                    cell.source = ''

        # Convert to help
        html, resources = HTMLExporter(template_file='basic').from_notebook_node(result)

        # Compose reply
        #model = km.kernel_model(kernel_id)
        #location = url_path_join(self.base_url, 'api', 'kernels', url_escape(kernel_id))
        #self.set_header('Location', location)
        self.set_status(201)
        print (html)
        self.set_header('Content-Type', 'text/html')
        self.write('<h1>Hello maarten</h1>')
        # self.finish(html)
        #self.finish(json.dumps(model, default=date_default))

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
