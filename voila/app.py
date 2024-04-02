#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################
import errno
import gettext
import json
import logging
import os
import random
import shutil
import signal
import socket
import sys
import tempfile
import threading
import webbrowser

from .tornado.contentshandler import VoilaContentsHandler

from .voila_identity_provider import VoilaLoginHandler

try:
    from urllib.parse import urljoin
    from urllib.request import pathname2url
except ImportError:
    from urllib import pathname2url

    from urlparse import urljoin

import jinja2
import tornado.ioloop
import tornado.web
from jupyter_core.paths import jupyter_config_path, jupyter_path
from jupyter_server.base.handlers import FileFindHandler, path_regex
from jupyter_server.config_manager import recursive_update
from jupyter_server.services.config.manager import ConfigManager
from jupyter_server.services.contents.largefilemanager import LargeFileManager
from jupyter_server.services.kernels.handlers import KernelHandler
from jupyter_server.services.kernels.websocket import KernelWebsocketHandler
from jupyter_server.auth.authorizer import AllowAllAuthorizer, Authorizer
from jupyter_server.auth.identity import PasswordIdentityProvider
from jupyter_server import DEFAULT_TEMPLATE_PATH_LIST, DEFAULT_STATIC_FILES_PATH
from jupyter_server.services.kernels.connection.base import (
    BaseKernelWebsocketConnection,
)
from jupyter_server.services.kernels.connection.channels import (
    ZMQChannelsWebsocketConnection,
)
from jupyter_server.auth.identity import (
    IdentityProvider,
)
from jupyter_server.utils import url_path_join
from jupyter_core.utils import run_sync

from jupyterlab_server.themes_handler import ThemesHandler


from traitlets import (
    Bool,
    Callable,
    Dict,
    Integer,
    List,
    Unicode,
    default,
    Type,
    Bytes,
    validate,
)
from traitlets.config.application import Application
from traitlets.config.loader import Config
from warnings import warn

from ._version import __version__
from .configuration import VoilaConfiguration
from .execute import VoilaExecutor
from .exporter import VoilaExporter
from .paths import ROOT, STATIC_ROOT, collect_static_paths, collect_template_paths
from .request_info_handler import RequestInfoSocketHandler
from .shutdown_kernel_handler import VoilaShutdownKernelHandler
from .static_file_handler import (
    AllowListFileHandler,
    MultiStaticFileHandler,
    TemplateStaticFileHandler,
)
from .tornado.handler import TornadoVoilaHandler
from .tornado.treehandler import TornadoVoilaTreeHandler
from .utils import create_include_assets_functions, get_data_dir, pjoin
from .voila_kernel_manager import voila_kernel_manager_factory

_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"


def _(x):
    return x


class Voila(Application):
    name = "voila"
    version = __version__
    examples = "voila example.ipynb --port 8888"

    flags = {
        "debug": (
            {
                "Voila": {"log_level": logging.DEBUG},
                "VoilaConfiguration": {"show_tracebacks": True},
            },
            _(
                "Set the log level to logging.DEBUG, and show exception tracebacks in output."
            ),
        ),
        "no-browser": (
            {"Voila": {"open_browser": False}},
            _("Don't open the notebook in a browser after startup."),
        ),
        "show-margins": (
            {
                "VoilaConfiguration": {"show_margins": True},
            },
            _(
                'Show left and right margins for the "lab" template, this gives a "classic" template look'
            ),
        ),
        "token": (
            {"Voila": {"auto_token": True}},
            _(""),
        ),
        "classic-tree": (
            {
                "VoilaConfiguration": {"classic_tree": True},
            },
            _("Use the jinja2-based tree page instead of the new JupyterLab-based one"),
        ),
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
    port = Integer(8866, config=True, help=_("Port of the Voilà server. Default 8866."))
    autoreload = Bool(
        False,
        config=True,
        help=_(
            "Will autoreload to server and the page when a template, js file or Python code changes"
        ),
    )
    root_dir = Unicode(config=True, help=_("The directory to use for notebooks."))
    static_root = Unicode(
        STATIC_ROOT,
        config=True,
        help=_("Directory holding static assets (HTML, JS and CSS files)."),
    )
    aliases = {
        "autoreload": "Voila.autoreload",
        "base_url": "Voila.base_url",
        "port": "Voila.port",
        "static": "Voila.static_root",
        "server_url": "Voila.server_url",
        "token": "Voila.token",
        "pool_size": "VoilaConfiguration.default_pool_size",
        "show_tracebacks": "VoilaConfiguration.show_tracebacks",
        "preheat_kernel": "VoilaConfiguration.preheat_kernel",
        "strip_sources": "VoilaConfiguration.strip_sources",
        "template": "VoilaConfiguration.template",
        "theme": "VoilaConfiguration.theme",
        "classic_tree": "VoilaConfiguration.classic_tree",
        "kernel_spec_manager_class": "VoilaConfiguration.kernel_spec_manager_class",
    }
    classes = [VoilaConfiguration, VoilaExecutor, VoilaExporter]
    connection_dir_root = Unicode(
        config=True,
        help=_(
            "Location of temporary connection files. Defaults "
            "to system `tempfile.gettempdir()` value."
        ),
    )
    connection_dir = Unicode()

    base_url = Unicode(
        "/",
        config=True,
        help=_(
            "Path for Voilà API calls. If server_url is unset, this will be \
            used for both the base route of the server and the client. \
            If server_url is set, the server will server the routes prefixed \
            by server_url, while the client will prefix by base_url (this is \
            useful in reverse proxies)."
        ),
    )

    server_url = Unicode(
        None,
        config=True,
        allow_none=True,
        help=_(
            "Path to prefix to Voilà API handlers. Leave unset to default to base_url"
        ),
    )

    notebook_path = Unicode(
        None,
        config=True,
        allow_none=True,
        help=_("path to notebook to serve with Voilà"),
    )

    template_paths = List([], config=True, help=_("path to jinja2 templates"))

    static_paths = List([STATIC_ROOT], config=True, help=_("paths to static assets"))

    mathjax_config = Unicode(  # TODO remove in 1.0.0
        None,
        allow_none=True,
        help="""
        Mathjax default configuration
        """,
    ).tag(config=True)

    mathjax_url = Unicode(  # TODO remove in 1.0.0
        None,
        allow_none=True,
        help="""
        URL to load Mathjax from.

        Defaults to loading from cdnjs.
        """,
    ).tag(config=True)

    port_retries = Integer(
        50,
        config=True,
        help=_(
            "The number of additional ports to try if the specified port is not available."
        ),
    )

    ip = Unicode(
        "localhost",
        config=True,
        help=_("The IP address the notebook server will listen on."),
    )

    open_browser = Bool(
        True,
        config=True,
        help=_(
            """Whether to open in a browser after starting.
                        The specific browser used is platform dependent and
                        determined by the python standard library `webbrowser`
                        module, unless it is overridden using the --browser
                        (NotebookApp.browser) configuration option.
                        """
        ),
    )

    browser = Unicode(
        "",
        config=True,
        help="""Specify what command to use to invoke a web
                      browser when opening the notebook. If not specified, the
                      default browser will be determined by the `webbrowser`
                      standard library module, which allows setting of the
                      BROWSER environment variable to override it.
                      """,
    )

    webbrowser_open_new = Integer(
        2,
        config=True,
        help=_(
            """Specify Where to open the notebook on startup. This is the
                                  `new` argument passed to the standard library method `webbrowser.open`.
                                  The behaviour is not guaranteed, but depends on browser support. Valid
                                  values are:
                                  - 2 opens a new tab,
                                  - 1 opens a new window,
                                  - 0 opens in an existing window.
                                  See the `webbrowser.open` documentation for details.
                                  """
        ),
    )

    custom_display_url = Unicode(
        "",
        config=True,
        help=_(
            """Override URL shown to users.
                                 Replace actual URL, including protocol, address, port and base URL,
                                 with the given value when displaying URL to the users. Do not change
                                 the actual connection URL. If authentication token is enabled, the
                                 token is added to the custom URL automatically.
                                 This option is intended to be used when the URL to display to the user
                                 cannot be determined reliably by the Jupyter notebook server (proxified
                                 or containerized setups for example)."""
        ),
    )

    prelaunch_hook = Callable(
        default_value=None,
        allow_none=True,
        config=True,
        help=_(
            """A function that is called prior to the launch of a new kernel instance
            when a user visits the voila webpage. Used for custom user authorization
            or any other necessary pre-launch functions.

            Should be of the form:

            def hook(req: tornado.web.RequestHandler,
                    notebook: nbformat.NotebookNode,
                    cwd: str)

            Although most customizations can leverage templates, if you need access
            to the request object (e.g. to inspect cookies for authentication),
            or to modify the notebook itself (e.g. to inject some custom structure,
            although much of this can be done by interacting with the kernel
            in javascript) the prelaunch hook lets you do that.
            """
        ),
    )

    cookie_secret = Bytes(
        b"",
        config=True,
        help="""The random bytes used to secure cookies.
        By default this is a new random number every time you start the server.
        Set it to a value in a config file to enable logins to persist across server sessions.

        Note: Cookie secrets should be kept private, do not share config files with
        cookie_secret stored in plaintext (you can read the value from a file).
        """,
    )

    token = Unicode(None, help="""Token for identity provider """, allow_none=True).tag(
        config=True
    )

    auto_token = Bool(
        False, help="""Generate token automatically """, allow_none=True
    ).tag(config=True)

    @default("cookie_secret")
    def _default_cookie_secret(self):
        return os.urandom(32)

    authorizer_class = Type(
        default_value=AllowAllAuthorizer,
        klass=Authorizer,
        config=True,
        help=_("The authorizer class to use."),
    )

    identity_provider_class = Type(
        default_value=PasswordIdentityProvider,
        klass=IdentityProvider,
        config=True,
        help=_("The identity provider class to use."),
    )

    kernel_websocket_connection_class = Type(
        default_value=ZMQChannelsWebsocketConnection,
        klass=BaseKernelWebsocketConnection,
        config=True,
        help=_("The kernel websocket connection class to use."),
    )

    @property
    def display_url(self):
        if self.custom_display_url:
            url = self.custom_display_url
            if not url.endswith("/"):
                url += "/"
        else:
            ip = "%s" % socket.gethostname() if self.ip in ("", "0.0.0.0") else self.ip
            url = self._url(ip)
        # TODO: do we want to have the token?
        if self.identity_provider.token:
            # Don't log full token if it came from config
            token = (
                self.identity_provider.token
                if self.identity_provider.token_generated
                else "..."
            )
            query = f"?token={token}"
        else:
            query = ""
        return f"{url}{query}"

    @property
    def connection_url(self):
        ip = self.ip if self.ip else "localhost"
        return self._url(ip)

    def _url(self, ip):
        # TODO: https / certfile
        # proto = 'https' if self.certfile else 'http'
        proto = "http"
        return "%s://%s:%i%s" % (proto, ip, self.port, self.base_url)

    config_file_paths = List(
        Unicode(), config=True, help=_("Paths to search for voila.(py|json)")
    )

    tornado_settings = Dict(
        {},
        config=True,
        help=_(
            "Extra settings to apply to tornado application, e.g. headers, ssl, etc"
        ),
    )

    @default("config_file_paths")
    def _config_file_paths_default(self):
        return [os.getcwd(), *jupyter_config_path()]

    @default("connection_dir_root")
    def _default_connection_dir(self):
        connection_dir = tempfile.gettempdir()
        self.log.info("Using %s to store connection files" % connection_dir)
        return connection_dir

    @default("log_level")
    def _default_log_level(self):
        return logging.INFO

    @property
    def labextensions_path(self):
        return jupyter_path("labextensions")

    @property
    def data_dir(self):
        return get_data_dir()

    @property
    def schemas_dir(self):
        return pjoin(self.data_dir, "schemas")

    @property
    def themes_dir(self):
        return pjoin(self.data_dir, "themes")

    @default("root_dir")
    def _default_root_dir(self):
        if self.notebook_path:
            return os.path.dirname(os.path.abspath(self.notebook_path))
        else:
            return os.getcwd()

    @validate("mathjax_url")
    def _valid_mathjax_url(self, proposal):
        warn(
            "Voila.mathjax_url is deprecated, this option will be removed in the next major release.",
            DeprecationWarning,
            stacklevel=2,
        )
        return proposal["value"]

    @validate("mathjax_config")
    def _valid_mathjax_config(self, proposal):
        warn(
            "Voila.mathjax_config is deprecated, this option will be removed in the next major release.",
            DeprecationWarning,
            stacklevel=2,
        )
        return proposal["value"]

    def _init_asyncio_patch(self):
        """set default asyncio policy to be compatible with tornado
        Tornado 6 (at least) is not compatible with the default
        asyncio implementation on Windows
        Pick the older SelectorEventLoopPolicy on Windows
        if the known-incompatible default policy is in use.
        do this as early as possible to make it a low priority and overridable
        ref: https://github.com/tornadoweb/tornado/issues/2608
        FIXME: if/when tornado supports the defaults in asyncio,
               remove and bump tornado requirement for py38
        """
        if sys.platform.startswith("win") and sys.version_info >= (3, 8):
            import asyncio

            try:
                from asyncio import (
                    WindowsProactorEventLoopPolicy,
                    WindowsSelectorEventLoopPolicy,
                )
            except ImportError:
                pass
                # not affected
            else:
                if (
                    type(asyncio.get_event_loop_policy())
                    is WindowsProactorEventLoopPolicy
                ):
                    # WindowsProactorEventLoopPolicy is not compatible with tornado 6
                    # fallback to the pre-3.8 default of Selector
                    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    def initialize(self, argv=None):
        self._init_asyncio_patch()
        self.log.debug("Searching path %s for config files", self.config_file_paths)
        # to make config_file_paths settable via cmd line, we first need to parse it
        super().initialize(argv)
        if len(self.extra_args) == 1:
            arg = self.extra_args[0]
            # I am not sure why we need to check if self.notebook_path is set, can we get rid of this?
            if not self.notebook_path:
                if os.path.isdir(arg):
                    self.root_dir = arg
                elif os.path.isfile(arg):
                    self.notebook_path = arg
                else:
                    raise ValueError(
                        "argument is neither a file nor a directory: %r" % arg
                    )
        elif len(self.extra_args) != 0:
            raise ValueError("provided more than 1 argument: %r" % self.extra_args)

        # then we load the config
        self.load_config_file("voila", path=self.config_file_paths)
        # common configuration options between the server extension and the application
        self.voila_configuration = VoilaConfiguration(parent=self)
        self.setup_template_dirs()
        signal.signal(signal.SIGTERM, self._handle_signal_stop)

    def setup_template_dirs(self):
        if self.voila_configuration.template:
            template_name = self.voila_configuration.template
            self.template_paths = collect_template_paths(
                ["voila", "nbconvert"], template_name, prune=True
            )
            self.static_paths = collect_static_paths(
                ["voila", "nbconvert"], template_name
            )
            self.static_paths.append(DEFAULT_STATIC_FILES_PATH)
            conf_paths = [os.path.join(d, "conf.json") for d in self.template_paths]
            for p in conf_paths:
                # see if config file exists
                if os.path.exists(p):
                    # load the template-related config
                    with open(p) as json_file:
                        conf = json.load(json_file)
                    # update the overall config with it, preserving CLI config priority
                    if "traitlet_configuration" in conf:
                        recursive_update(
                            conf["traitlet_configuration"],
                            self.voila_configuration.config.VoilaConfiguration,
                        )
                        # pass merged config to overall Voilà config
                        self.voila_configuration.config.VoilaConfiguration = Config(
                            conf["traitlet_configuration"]
                        )
        self.log.debug("using template: %s", self.voila_configuration.template)
        self.log.debug("template paths:\n\t%s", "\n\t".join(self.template_paths))
        self.log.debug("static paths:\n\t%s", "\n\t".join(self.static_paths))
        if self.notebook_path and not os.path.exists(self.notebook_path):
            raise ValueError("Notebook not found: %s" % self.notebook_path)

    def init_settings(self) -> Dict:
        """Initialize settings for Voila application."""
        # default server_url to base_url
        self.server_url = self.server_url or self.base_url

        self.kernel_spec_manager = self.voila_configuration.kernel_spec_manager_class(
            parent=self
        )

        # we create a config manager that load both the serverconfig and nbconfig (classical notebook)
        read_config_path = [
            os.path.join(p, "serverconfig") for p in jupyter_config_path()
        ]
        read_config_path += [os.path.join(p, "nbconfig") for p in jupyter_config_path()]
        self.config_manager = ConfigManager(
            parent=self, read_config_path=read_config_path
        )
        self.contents_manager = LargeFileManager(parent=self)
        preheat_kernel: bool = self.voila_configuration.preheat_kernel
        pool_size: int = self.voila_configuration.default_pool_size

        if preheat_kernel and self.prelaunch_hook:
            raise Exception("`preheat_kernel` and `prelaunch_hook` are incompatible")

        kernel_manager_class = voila_kernel_manager_factory(
            self.voila_configuration.multi_kernel_manager_class,
            preheat_kernel,
            pool_size,
        )
        self.kernel_manager = kernel_manager_class(
            parent=self,
            connection_dir=self.connection_dir,
            kernel_spec_manager=self.kernel_spec_manager,
            allowed_message_types=[
                "comm_open",
                "comm_close",
                "comm_msg",
                "comm_info_request",
                "kernel_info_request",
                "shutdown_request",
            ],
        )

        jenv_opt = {
            "autoescape": True
        }  # we might want extra options via cmd line like notebook server
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_paths),
            extensions=["jinja2.ext.i18n"],
            **jenv_opt,
        )
        server_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(DEFAULT_TEMPLATE_PATH_LIST),
            extensions=["jinja2.ext.i18n"],
            **jenv_opt,
        )

        nbui = gettext.translation(
            "nbui", localedir=os.path.join(ROOT, "i18n"), fallback=True
        )
        env.install_gettext_translations(nbui, newstyle=False)
        server_env.install_gettext_translations(nbui, newstyle=False)

        identity_provider_kwargs = {
            "parent": self,
            "log": self.log,
            "login_handler_class": VoilaLoginHandler,
        }
        if self.token is None and not self.auto_token:
            identity_provider_kwargs["token"] = ""
        elif self.token is not None:
            identity_provider_kwargs["token"] = self.token

        self.identity_provider = self.identity_provider_class(
            **identity_provider_kwargs
        )

        self.authorizer = self.authorizer_class(
            parent=self, log=self.log, identity_provider=self.identity_provider
        )

        settings = dict(
            base_url=self.base_url,
            server_url=self.server_url or self.base_url,
            kernel_manager=self.kernel_manager,
            kernel_spec_manager=self.kernel_spec_manager,
            allow_remote_access=True,
            autoreload=self.autoreload,
            voila_jinja2_env=env,
            jinja2_env=server_env,
            server_root_dir="/",
            contents_manager=self.contents_manager,
            config_manager=self.config_manager,
            cookie_secret=self.cookie_secret,
            authorizer=self.authorizer,
            identity_provider=self.identity_provider,
            kernel_websocket_connection_class=self.kernel_websocket_connection_class,
            login_url=url_path_join(self.base_url, "/login"),
            mathjax_config=self.mathjax_config,
            mathjax_url=self.mathjax_url,
        )
        settings[self.name] = self  # Why???

        return settings

    def init_handlers(self) -> List:
        """Initialize handlers for Voila application."""
        handlers = []
        tree_handler_conf = {"voila_configuration": self.voila_configuration}
        handlers.extend(
            [
                (
                    url_path_join(
                        self.server_url, r"/api/kernels/%s" % _kernel_id_regex
                    ),
                    KernelHandler,
                ),
                (
                    url_path_join(
                        self.server_url, r"/api/kernels/%s/channels" % _kernel_id_regex
                    ),
                    KernelWebsocketHandler,
                ),
                (
                    url_path_join(self.server_url, r"/voila/templates/(.*)"),
                    TemplateStaticFileHandler,
                ),
                (
                    url_path_join(self.server_url, r"/voila/static/(.*)"),
                    MultiStaticFileHandler,
                    {"paths": self.static_paths, "default_filename": "index.html"},
                ),
                (
                    url_path_join(self.server_url, r"/voila/api/themes/(.*)"),
                    ThemesHandler,
                    {
                        "themes_url": "/voila/api/themes",
                        "path": self.themes_dir,
                        "labextensions_path": jupyter_path("labextensions"),
                        "no_cache_paths": ["/"],
                    },
                ),
                (
                    url_path_join(self.server_url, r"/voila/api/shutdown/(.*)"),
                    VoilaShutdownKernelHandler,
                ),
            ]
        )
        handlers.extend(self.identity_provider.get_handlers())
        if self.voila_configuration.preheat_kernel:
            handlers.append(
                (
                    url_path_join(
                        self.server_url, r"/voila/query/%s" % _kernel_id_regex
                    ),
                    RequestInfoSocketHandler,
                )
            )
        # Serving JupyterLab extensions
        handlers.append(
            (
                url_path_join(self.server_url, r"/voila/labextensions/(.*)"),
                FileFindHandler,
                {
                    "path": self.labextensions_path,
                    "no_cache_paths": ["/"],  # don't cache anything in labextensions
                },
            )
        )
        handlers.append(
            (
                url_path_join(self.server_url, r"/voila/files/(.*)"),
                AllowListFileHandler,
                {
                    "allowlist": self.voila_configuration.file_allowlist,
                    "denylist": self.voila_configuration.file_denylist,
                    "path": self.root_dir,
                },
            )
        )

        if self.notebook_path:
            handlers.append(
                (
                    url_path_join(self.server_url, r"/(.*)"),
                    TornadoVoilaHandler,
                    {
                        "notebook_path": os.path.relpath(
                            self.notebook_path, self.root_dir
                        ),
                        "template_paths": self.template_paths,
                        "config": self.config,
                        "voila_configuration": self.voila_configuration,
                        "prelaunch_hook": self.prelaunch_hook,
                    },
                )
            )
        else:
            self.log.debug("serving directory: %r", self.root_dir)
            handlers.extend(
                [
                    (self.server_url, TornadoVoilaTreeHandler, tree_handler_conf),
                    (
                        url_path_join(self.server_url, r"/voila/tree" + path_regex),
                        TornadoVoilaTreeHandler,
                        tree_handler_conf,
                    ),
                    (
                        url_path_join(self.server_url, r"/voila/render/(.*)"),
                        TornadoVoilaHandler,
                        {
                            "template_paths": self.template_paths,
                            "config": self.config,
                            "voila_configuration": self.voila_configuration,
                            "prelaunch_hook": self.prelaunch_hook,
                        },
                    ),
                    # On serving a directory, expose the content handler.
                    (
                        url_path_join(
                            self.server_url, r"/voila/api/contents%s" % path_regex
                        ),
                        VoilaContentsHandler,
                        tree_handler_conf,
                    ),
                ]
            )
        return handlers

    def start(self):
        self.connection_dir = tempfile.mkdtemp(
            prefix="voila_", dir=self.connection_dir_root
        )
        self.log.info("Storing connection files in %s." % self.connection_dir)
        self.log.info("Serving static files from %s." % self.static_root)

        settings = self.init_settings()

        self.app = tornado.web.Application(**settings)
        self.app.settings.update(self.tornado_settings)
        handlers = self.init_handlers()
        self.app.add_handlers(".*$", handlers)
        self.listen()

    def _handle_signal_stop(self, sig, frame):
        self.log.info("Handle signal %s." % sig)
        self.ioloop.add_callback_from_signal(self.ioloop.stop)

    def stop(self):
        shutil.rmtree(self.connection_dir)
        run_sync(self.kernel_manager.shutdown_all)()

    def random_ports(self, port, n):
        """Generate a list of n random ports near the given port.

        The first 5 ports will be sequential, and the remaining n-5 will be
        randomly selected in the range [port-2*n, port+2*n].
        """
        for i in range(min(5, n)):
            yield port + i
        for i in range(n - 5):
            yield max(1, port + random.randint(-2 * n, 2 * n))

    def listen(self):
        success = False
        for port in self.random_ports(self.port, self.port_retries + 1):
            try:
                self.app.listen(port, self.ip)
                self.port = port
                self.log.info("Voilà is running at:\n%s" % self.display_url)
            except OSError as e:
                if e.errno == errno.EADDRINUSE:
                    self.log.info(
                        _("The port %i is already in use, trying another port.") % port
                    )
                    continue
                elif e.errno in (
                    errno.EACCES,
                    getattr(errno, "WSAEACCES", errno.EACCES),
                ):
                    self.log.warning(_("Permission to listen on port %i denied") % port)
                    continue
                else:
                    raise
            else:
                self.port = port
                success = True
                break

        if not success:
            self.log.critical(
                _(
                    "ERROR: the Voilà server could not be started because "
                    "no available port could be found."
                )
            )
            self.exit(1)

        if self.open_browser:
            self.launch_browser()

        self.ioloop = tornado.ioloop.IOLoop.current()
        try:
            self.ioloop.start()
        except KeyboardInterrupt:
            self.log.info("Stopping...")
        finally:
            self.stop()

    def launch_browser(self):
        try:
            browser = webbrowser.get(self.browser or None)
        except webbrowser.Error as e:
            self.log.warning(_("No web browser found: %s.") % e)
            browser = None

        if not browser:
            return

        uri = self.base_url
        fd, open_file = tempfile.mkstemp(suffix=".html")
        # Write a temporary file to open in the browser
        with open(fd, "w", encoding="utf-8") as fh:
            url = url_path_join(self.connection_url, uri)

            include_assets_functions = create_include_assets_functions(
                self.voila_configuration.template, url
            )

            jinja2_env = self.app.settings["voila_jinja2_env"]
            template = jinja2_env.get_template("browser-open.html")
            fh.write(
                template.render(
                    open_url=url,
                    base_url=url,
                    theme=self.voila_configuration.theme,
                    **include_assets_functions,
                )
            )

        def target():
            return browser.open(
                urljoin("file:", pathname2url(open_file)), new=self.webbrowser_open_new
            )

        threading.Thread(target=target).start()


main = Voila.launch_instance
