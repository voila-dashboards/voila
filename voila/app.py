#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

from zmq.eventloop import ioloop
import os
import shutil
import signal
import tempfile
import logging
import gettext

import jinja2

import tornado.ioloop
import tornado.web

from traitlets.config.application import Application
from traitlets import Unicode, Integer, Bool, List, default

from jupyter_server.services.kernels.kernelmanager import MappingKernelManager
from jupyter_server.services.kernels.handlers import KernelHandler, ZMQChannelsHandler
from jupyter_server.base.handlers import path_regex
from jupyter_server.services.contents.largefilemanager import LargeFileManager
from jupyter_server.utils import url_path_join
from jupyter_server.services.config import ConfigManager
from jupyter_server.base.handlers import FileFindHandler
from jupyter_core.paths import jupyter_config_path, jupyter_path
from ipython_genutils.py3compat import getcwd

from .paths import ROOT, STATIC_ROOT, collect_template_paths
from .handler import VoilaHandler
from .treehandler import VoilaTreeHandler
from ._version import __version__
from .static_file_handler import MultiStaticFileHandler

ioloop.install()
_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"


class Voila(Application):
    name = 'voila'
    version = __version__
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
    root_dir = Unicode(config=True, help="The directory to use for notebooks.")
    static_root = Unicode(
        STATIC_ROOT,
        config=True,
        help='Directory holding static assets (HTML, JS and CSS files).'
    )
    aliases = {
        'port': 'Voila.port',
        'static': 'Voila.static_root',
        'strip_sources': 'Voila.strip_sources',
        'autoreload': 'Voila.autoreload',
        'template': 'Voila.template'
    }
    connection_dir_root = Unicode(
        config=True,
        help=(
            'Location of temporry connection files. Defaults '
            'to system `tempfile.gettempdir()` value.'
        )
    )
    connection_dir = Unicode()

    template = Unicode(
        'default',
        config=True,
        allow_none=True,
        help=(
            'template name to be used by voila.'
        )
    )

    notebook_path = Unicode(
        None,
        config=True,
        allow_none=True,
        help=(
            'path to notebook to serve with voila')
    )

    nbconvert_template_paths = List(
        [],
        config=True,
        help=(
            'path to nbconvert templates'
        )
    )

    template_paths = List(
        [],
        allow_none=True,
        config=True,
        help=(
            'path to nbconvert templates'
        )
    )

    static_paths = List(
        [STATIC_ROOT],
        config=True,
        help=(
            'paths to static assets'
        )
    )

    @default('connection_dir_root')
    def _default_connection_dir(self):
        connection_dir = tempfile.gettempdir()
        self.log.info('Using %s to store connection files' % connection_dir)
        return connection_dir

    @default('log_level')
    def _default_log_level(self):
        return logging.INFO

    # similar to NotebookApp, except no extra path
    @property
    def nbextensions_path(self):
        """The path to look for Javascript notebook extensions"""
        path = jupyter_path('nbextensions')
        # FIXME: remove IPython nbextensions path after a migration period
        try:
            from IPython.paths import get_ipython_dir
        except ImportError:
            pass
        else:
            path.append(os.path.join(get_ipython_dir(), 'nbextensions'))
        return path

    @default('root_dir')
    def _default_root_dir(self):
        if self.notebook_path:
            return os.path.dirname(os.path.abspath(self.notebook_path))
        else:
            return getcwd()

    def initialize(self, argv=None):
        super(Voila, self).initialize(argv)
        signal.signal(signal.SIGTERM, self._handle_signal_stop)

    def parse_command_line(self, argv=None):
        super(Voila, self).parse_command_line(argv)

    def setup_template_dirs(self):
        self.notebook_path = self.notebook_path if self.notebook_path else self.extra_args[0] if len(self.extra_args) == 1 else None
        if self.template:
            collect_template_paths(
                self.nbconvert_template_paths,
                self.static_paths,
                self.template_paths,
                self.template)
        self.log.debug('using template: %s', self.template)
        self.log.debug('nbconvert template paths: %s', self.nbconvert_template_paths)
        self.log.debug('template paths: %s', self.template_paths)
        self.log.debug('static paths: %s', self.static_paths)
        if self.notebook_path and not os.path.exists(self.notebook_path):
            raise ValueError('Notebook not found: %s' % self.notebook_path)

    def _handle_signal_stop(self, sig, frame):
        self.log.info('Handle signal %s.' % sig)
        self.ioloop.add_callback_from_signal(self.ioloop.stop)

    def start(self):
        self.setup_template_dirs()
        self.connection_dir = tempfile.mkdtemp(
            prefix='voila_',
            dir=self.connection_dir_root
        )
        self.log.info('Storing connection files in %s.' % self.connection_dir)
        self.log.info('Serving static files from %s.' % self.static_root)

        self.kernel_manager = MappingKernelManager(
            connection_dir=self.connection_dir,
            allowed_message_types=[
                'comm_msg',
                'comm_info_request',
                'kernel_info_request',
                'shutdown_request'
            ]
        )

        jenv_opt = {"autoescape": True}  # we might want extra options via cmd line like notebook server
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.template_paths), extensions=['jinja2.ext.i18n'], **jenv_opt)
        nbui = gettext.translation('nbui', localedir=os.path.join(ROOT, 'i18n'), fallback=True)
        env.install_gettext_translations(nbui, newstyle=False)
        contents_manager = LargeFileManager(parent=self)  # TODO: make this configurable like notebook

        # we create a config manager that load both the serverconfig and nbconfig (classical notebook)
        read_config_path = [os.path.join(p, 'serverconfig') for p in jupyter_config_path()]
        read_config_path += [os.path.join(p, 'nbconfig') for p in jupyter_config_path()]
        self.config_manager = ConfigManager(parent=self, read_config_path=read_config_path)

        self.app = tornado.web.Application(
            kernel_manager=self.kernel_manager,
            allow_remote_access=True,
            autoreload=self.autoreload,
            voila_jinja2_env=env,
            jinja2_env=env,
            static_path='/',
            server_root_dir='/',
            contents_manager=contents_manager,
            config_manager=self.config_manager
        )

        base_url = self.app.settings.get('base_url', '/')

        handlers = []

        handlers.extend([
            (url_path_join(base_url, r'/api/kernels/%s' % _kernel_id_regex), KernelHandler),
            (url_path_join(base_url, r'/api/kernels/%s/channels' % _kernel_id_regex), ZMQChannelsHandler),
            (
                url_path_join(base_url, r'/voila/static/(.*)'),
                MultiStaticFileHandler,
                {
                    'paths': self.static_paths,
                    'default_filename': 'index.html'
                }
            )
        ])

        # this handler serves the nbextensions similar to the classical notebook
        handlers.append(
            (
                url_path_join(base_url, r'/voila/nbextensions/(.*)'),
                FileFindHandler,
                {
                    'path': self.nbextensions_path,
                    'no_cache_paths': ['/'],  # don't cache anything in nbextensions
                },
            )
        )

        if self.notebook_path:
            handlers.append((
                url_path_join(base_url, r'/'),
                VoilaHandler,
                {
                    'notebook_path': os.path.relpath(self.notebook_path, self.root_dir),
                    'strip_sources': self.strip_sources,
                    'nbconvert_template_paths': self.nbconvert_template_paths,
                    'config': self.config
                }
            ))
        else:
            handlers.extend([
                (base_url, VoilaTreeHandler),
                (url_path_join(base_url, r'/voila/tree' + path_regex), VoilaTreeHandler),
                (url_path_join(base_url, r'/voila/render' + path_regex), VoilaHandler, {'strip_sources': self.strip_sources}),
            ])

        self.app.add_handlers('.*$', handlers)
        self.listen()

    def listen(self):
        self.app.listen(self.port)
        self.log.info('Voila listening on port %s.' % self.port)

        self.ioloop = tornado.ioloop.IOLoop.current()
        try:
            self.ioloop.start()
        except KeyboardInterrupt:
            self.log.info('Stopping...')
        finally:
            shutil.rmtree(self.connection_dir)
            self.kernel_manager.shutdown_all()


main = Voila.launch_instance
