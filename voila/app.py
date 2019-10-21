#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

from zmq.eventloop import ioloop

import gettext
import io
import logging
import threading
import tempfile
import os
import shutil
import signal
import socket
import webbrowser
import errno
import random

try:
    from urllib.parse import urljoin
    from urllib.request import pathname2url
except ImportError:
    from urllib import pathname2url
    from urlparse import urljoin

import jinja2

import tornado.ioloop
import tornado.web

from traitlets.config.application import Application
from traitlets import Unicode, Integer, Bool, Dict, List, default

from jupyter_server.services.kernels.kernelmanager import MappingKernelManager
from jupyter_server.services.kernels.handlers import KernelHandler, ZMQChannelsHandler
from jupyter_server.services.contents.largefilemanager import LargeFileManager
from jupyter_server.base.handlers import path_regex
from jupyter_server.utils import url_path_join
from jupyter_server.services.config import ConfigManager
from jupyter_server.base.handlers import FileFindHandler

from jupyter_client.kernelspec import KernelSpecManager

from jupyter_core.paths import jupyter_config_path, jupyter_path

from ipython_genutils.py3compat import getcwd

from .paths import ROOT, STATIC_ROOT, collect_template_paths
from .handler import VoilaHandler
from .treehandler import VoilaTreeHandler
from ._version import __version__
from .static_file_handler import MultiStaticFileHandler, WhiteListFileHandler
from .configuration import VoilaConfiguration
from .execute import VoilaExecutePreprocessor
from .exporter import VoilaExporter
from .csspreprocessor import VoilaCSSPreprocessor

ioloop.install()
_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"


def _(x):
    return x


class Voila(Application):
    name = 'voila'
    version = __version__
    examples = 'voila example.ipynb --port 8888'

    flags = {
        'debug': ({'Voila': {'log_level': logging.DEBUG}}, _("Set the log level to logging.DEBUG")),
        'no-browser': ({'Voila': {'open_browser': False}}, _('Don\'t open the notebook in a browser after startup.'))
    }

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
    port = Integer(
        8866,
        config=True,
        help=_(
            'Port of the voila server. Default 8866.'
        )
    )
    autoreload = Bool(
        False,
        config=True,
        help=_(
            'Will autoreload to server and the page when a template, js file or Python code changes'
        )
    )
    root_dir = Unicode(config=True, help=_('The directory to use for notebooks.'))
    static_root = Unicode(
        STATIC_ROOT,
        config=True,
        help=_(
            'Directory holding static assets (HTML, JS and CSS files).'
        )
    )
    aliases = {
        'port': 'Voila.port',
        'static': 'Voila.static_root',
        'strip_sources': 'VoilaConfiguration.strip_sources',
        'autoreload': 'Voila.autoreload',
        'template': 'VoilaConfiguration.template',
        'theme': 'VoilaConfiguration.theme',
        'base_url': 'Voila.base_url',
        'server_url': 'Voila.server_url',
        'enable_nbextensions': 'VoilaConfiguration.enable_nbextensions'
    }
    classes = [
        VoilaConfiguration,
        VoilaExecutePreprocessor,
        VoilaExporter,
        VoilaCSSPreprocessor
    ]
    connection_dir_root = Unicode(
        config=True,
        help=_(
            'Location of temporry connection files. Defaults '
            'to system `tempfile.gettempdir()` value.'
        )
    )
    connection_dir = Unicode()

    base_url = Unicode(
        '/',
        config=True,
        help=_(
            'Path for voila API calls. If server_url is unset, this will be \
            used for both the base route of the server and the client. \
            If server_url is set, the server will server the routes prefixed \
            by server_url, while the client will prefix by base_url (this is \
            useful in reverse proxies).'
        )
    )

    server_url = Unicode(
        None,
        config=True,
        allow_none=True,
        help=_(
            'Path to prefix to voila API handlers. Leave unset to default to base_url'
        )
    )

    notebook_path = Unicode(
        None,
        config=True,
        allow_none=True,
        help=_(
            'path to notebook to serve with voila'
        )
    )

    nbconvert_template_paths = List(
        [],
        config=True,
        help=_(
            'path to nbconvert templates'
        )
    )

    template_paths = List(
        [],
        allow_none=True,
        config=True,
        help=_(
            'path to nbconvert templates'
        )
    )

    static_paths = List(
        [STATIC_ROOT],
        config=True,
        help=_(
            'paths to static assets'
        )
    )

    port_retries = Integer(50, config=True,
                           help=_("The number of additional ports to try if the specified port is not available.")
                           )

    ip = Unicode('localhost', config=True,
                 help=_("The IP address the notebook server will listen on."))

    open_browser = Bool(True, config=True,
                        help=_("""Whether to open in a browser after starting.
                        The specific browser used is platform dependent and
                        determined by the python standard library `webbrowser`
                        module, unless it is overridden using the --browser
                        (NotebookApp.browser) configuration option.
                        """))

    browser = Unicode(u'', config=True,
                      help="""Specify what command to use to invoke a web
                      browser when opening the notebook. If not specified, the
                      default browser will be determined by the `webbrowser`
                      standard library module, which allows setting of the
                      BROWSER environment variable to override it.
                      """)

    webbrowser_open_new = Integer(2, config=True,
                                  help=_("""Specify Where to open the notebook on startup. This is the
                                  `new` argument passed to the standard library method `webbrowser.open`.
                                  The behaviour is not guaranteed, but depends on browser support. Valid
                                  values are:
                                  - 2 opens a new tab,
                                  - 1 opens a new window,
                                  - 0 opens in an existing window.
                                  See the `webbrowser.open` documentation for details.
                                  """))

    custom_display_url = Unicode(u'', config=True,
                                 help=_("""Override URL shown to users.
                                 Replace actual URL, including protocol, address, port and base URL,
                                 with the given value when displaying URL to the users. Do not change
                                 the actual connection URL. If authentication token is enabled, the
                                 token is added to the custom URL automatically.
                                 This option is intended to be used when the URL to display to the user
                                 cannot be determined reliably by the Jupyter notebook server (proxified
                                 or containerized setups for example)."""))

    @property
    def display_url(self):
        if self.custom_display_url:
            url = self.custom_display_url
            if not url.endswith('/'):
                url += '/'
        else:
            if self.ip in ('', '0.0.0.0'):
                ip = "%s" % socket.gethostname()
            else:
                ip = self.ip
            url = self._url(ip)
        # TODO: do we want to have the token?
        # if self.token:
        #     # Don't log full token if it came from config
        #     token = self.token if self._token_generated else '...'
        #     url = (url_concat(url, {'token': token})
        #           + '\n or '
        #           + url_concat(self._url('127.0.0.1'), {'token': token}))
        return url

    @property
    def connection_url(self):
        ip = self.ip if self.ip else 'localhost'
        return self._url(ip)

    def _url(self, ip):
        # TODO: https / certfile
        # proto = 'https' if self.certfile else 'http'
        proto = 'http'
        return "%s://%s:%i%s" % (proto, ip, self.port, self.base_url)

    config_file_paths = List(
        Unicode(),
        config=True,
        help=_(
            'Paths to search for voila.(py|json)'
        )
    )

    tornado_settings = Dict(
        {},
        config=True,
        help=_(
            'Extra settings to apply to tornado application, e.g. headers, ssl, etc'
        )
    )

    @default('config_file_paths')
    def _config_file_paths_default(self):
        return [os.getcwd()] + jupyter_config_path()

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
        self.log.debug("Searching path %s for config files", self.config_file_paths)
        # to make config_file_paths settable via cmd line, we first need to parse it
        super(Voila, self).initialize(argv)
        if len(self.extra_args) == 1:
            arg = self.extra_args[0]
            # I am not sure why we need to check if self.notebook_path is set, can we get rid of this?
            if not self.notebook_path:
                if os.path.isdir(arg):
                    self.root_dir = arg
                elif os.path.isfile(arg):
                    self.notebook_path = arg
                else:
                    raise ValueError('argument is neither a file nor a directory: %r' % arg)
        elif len(self.extra_args) != 0:
            raise ValueError('provided more than 1 argument: %r' % self.extra_args)

        # then we load the config
        self.load_config_file('voila', path=self.config_file_paths)
        # but that cli config has preference, so we overwrite with that
        self.update_config(self.cli_config)
        # common configuration options between the server extension and the application
        self.voila_configuration = VoilaConfiguration(parent=self)
        self.setup_template_dirs()
        signal.signal(signal.SIGTERM, self._handle_signal_stop)

    def setup_template_dirs(self):
        if self.voila_configuration.template:
            collect_template_paths(
                self.nbconvert_template_paths,
                self.static_paths,
                self.template_paths,
                self.voila_configuration.template)
        self.log.debug('using template: %s', self.voila_configuration.template)
        self.log.debug('nbconvert template paths:\n\t%s', '\n\t'.join(self.nbconvert_template_paths))
        self.log.debug('template paths:\n\t%s', '\n\t'.join(self.template_paths))
        self.log.debug('static paths:\n\t%s', '\n\t'.join(self.static_paths))
        if self.notebook_path and not os.path.exists(self.notebook_path):
            raise ValueError('Notebook not found: %s' % self.notebook_path)

    def _handle_signal_stop(self, sig, frame):
        self.log.info('Handle signal %s.' % sig)
        self.ioloop.add_callback_from_signal(self.ioloop.stop)

    def start(self):
        self.connection_dir = tempfile.mkdtemp(
            prefix='voila_',
            dir=self.connection_dir_root
        )
        self.log.info('Storing connection files in %s.' % self.connection_dir)
        self.log.info('Serving static files from %s.' % self.static_root)

        self.kernel_spec_manager = KernelSpecManager(
            parent=self
        )

        self.kernel_manager = MappingKernelManager(
            parent=self,
            connection_dir=self.connection_dir,
            kernel_spec_manager=self.kernel_spec_manager,
            allowed_message_types=[
                'comm_open',
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
        self.contents_manager = LargeFileManager(parent=self)

        # we create a config manager that load both the serverconfig and nbconfig (classical notebook)
        read_config_path = [os.path.join(p, 'serverconfig') for p in jupyter_config_path()]
        read_config_path += [os.path.join(p, 'nbconfig') for p in jupyter_config_path()]
        self.config_manager = ConfigManager(parent=self, read_config_path=read_config_path)

        # default server_url to base_url
        self.server_url = self.server_url or self.base_url

        self.app = tornado.web.Application(
            base_url=self.base_url,
            server_url=self.server_url or self.base_url,
            kernel_manager=self.kernel_manager,
            kernel_spec_manager=self.kernel_spec_manager,
            allow_remote_access=True,
            autoreload=self.autoreload,
            voila_jinja2_env=env,
            jinja2_env=env,
            static_path='/',
            server_root_dir='/',
            contents_manager=self.contents_manager,
            config_manager=self.config_manager
        )

        self.app.settings.update(self.tornado_settings)

        handlers = []

        handlers.extend([
            (url_path_join(self.server_url, r'/api/kernels/%s' % _kernel_id_regex), KernelHandler),
            (url_path_join(self.server_url, r'/api/kernels/%s/channels' % _kernel_id_regex), ZMQChannelsHandler),
            (
                url_path_join(self.server_url, r'/voila/static/(.*)'),
                MultiStaticFileHandler,
                {
                    'paths': self.static_paths,
                    'default_filename': 'index.html'
                }
            )
        ])

        # Serving notebook extensions
        if self.voila_configuration.enable_nbextensions:
            handlers.append(
                (
                    url_path_join(self.server_url, r'/voila/nbextensions/(.*)'),
                    FileFindHandler,
                    {
                        'path': self.nbextensions_path,
                        'no_cache_paths': ['/'],  # don't cache anything in nbextensions
                    },
                )
            )
        handlers.append(
            (
                url_path_join(self.server_url, r'/voila/files/(.*)'),
                WhiteListFileHandler,
                {
                    'whitelist': self.voila_configuration.file_whitelist,
                    'blacklist': self.voila_configuration.file_blacklist,
                    'path': self.root_dir,
                },
            )
        )

        tree_handler_conf = {
            'voila_configuration': self.voila_configuration
        }
        if self.notebook_path:
            handlers.append((
                url_path_join(self.server_url, r'/(.*)'),
                VoilaHandler,
                {
                    'notebook_path': os.path.relpath(self.notebook_path, self.root_dir),
                    'nbconvert_template_paths': self.nbconvert_template_paths,
                    'config': self.config,
                    'voila_configuration': self.voila_configuration
                }
            ))
        else:
            self.log.debug('serving directory: %r', self.root_dir)
            handlers.extend([
                (self.server_url, VoilaTreeHandler, tree_handler_conf),
                (url_path_join(self.server_url, r'/voila/tree' + path_regex), VoilaTreeHandler, tree_handler_conf),
                (url_path_join(self.server_url, r'/voila/render/(.*)'), VoilaHandler,
                    {
                        'nbconvert_template_paths': self.nbconvert_template_paths,
                        'config': self.config,
                        'voila_configuration': self.voila_configuration
                    }),
            ])

        self.app.add_handlers('.*$', handlers)
        self.listen()

    def stop(self):
        shutil.rmtree(self.connection_dir)
        self.kernel_manager.shutdown_all()

    def random_ports(self, port, n):
        """Generate a list of n random ports near the given port.

        The first 5 ports will be sequential, and the remaining n-5 will be
        randomly selected in the range [port-2*n, port+2*n].
        """
        for i in range(min(5, n)):
            yield port + i
        for i in range(n-5):
            yield max(1, port + random.randint(-2*n, 2*n))

    def listen(self):
        for port in self.random_ports(self.port, self.port_retries+1):
            try:
                self.app.listen(port)
                self.port = port
                self.log.info('Voila is running at:\n%s' % self.display_url)
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    self.log.info(_('The port %i is already in use, trying another port.') % port)
                    continue
                elif e.errno in (errno.EACCES, getattr(errno, 'WSAEACCES', errno.EACCES)):
                    self.log.warning(_("Permission to listen on port %i denied") % port)
                    continue
                else:
                    raise
            else:
                self.port = port
                success = True
                break

        if not success:
            self.log.critical(_('ERROR: the voila server could not be started because '
                              'no available port could be found.'))
            self.exit(1)

        if self.open_browser:
            self.launch_browser()

        self.ioloop = tornado.ioloop.IOLoop.current()
        try:
            self.ioloop.start()
        except KeyboardInterrupt:
            self.log.info('Stopping...')
        finally:
            self.stop()

    def launch_browser(self):
        try:
            browser = webbrowser.get(self.browser or None)
        except webbrowser.Error as e:
            self.log.warning(_('No web browser found: %s.') % e)
            browser = None

        if not browser:
            return

        uri = self.base_url
        fd, open_file = tempfile.mkstemp(suffix='.html')
        # Write a temporary file to open in the browser
        with io.open(fd, 'w', encoding='utf-8') as fh:
            # TODO: do we want to have the token?
            # if self.token:
            #     url = url_concat(url, {'token': self.token})
            url = url_path_join(self.connection_url, uri)

            jinja2_env = self.app.settings['jinja2_env']
            template = jinja2_env.get_template('browser-open.html')
            fh.write(template.render(open_url=url, base_url=url))

        def target():
            return browser.open(urljoin('file:', pathname2url(open_file)), new=self.webbrowser_open_new)
        threading.Thread(target=target).start()


main = Voila.launch_instance
