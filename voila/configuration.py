#############################################################################
# Copyright (c) 2018, QuantStack                                            #
# Copyright (c) 2018, Voilà Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import traitlets.config
from traitlets import Bool, Callable, Dict, Enum, Int, List, Type, Unicode, validate

from warnings import warn


class VoilaConfiguration(traitlets.config.Configurable):
    """Common configuration options between the server extension and the application."""

    allow_template_override = Enum(
        ["YES", "NOTEBOOK", "NO"],
        "YES",
        help="""
    Allow overriding the template (YES), or not (NO), or only from the notebook metadata.
    """,
        config=True,
    )
    allow_theme_override = Enum(
        ["YES", "NOTEBOOK", "NO"],
        "YES",
        help="""
    Allow overriding the theme (YES), or not (NO), or only from the notebook metadata.
    """,
        config=True,
    )
    template = Unicode(
        "lab", config=True, allow_none=True, help=("template name to be used by voila.")
    )
    classic_tree = Bool(
        False,
        config=True,
        help=("Use the jinja2-based tree page instead of the new JupyterLab-based one"),
    )
    resources = Dict(
        allow_none=True,
        config=True,
        help="""
        extra resources used by templates;
        example use with --template=reveal
        --VoilaConfiguration.resources="{'reveal': {'transition': 'fade', 'scroll': True}}"
        """,
    )
    theme = Unicode("light", config=True)
    show_margins = Bool(
        False,
        config=True,
        help=(
            'Show left and right margins for the "lab" template, this gives a "classic" template look'
        ),
    )
    strip_sources = Bool(True, config=True, help="Strip sources from rendered html")

    file_allowlist = List(
        Unicode(),
        [r".*\.(png|jpg|gif|svg)"],
        config=True,
        help=r"""
    List of regular expressions for controlling which static files are served.
    All files that are served should at least match 1 allowlist rule, and no denylist rule
    Example: --VoilaConfiguration.file_allowlist="['.*\.(png|jpg|gif|svg)', 'public.*']"
    """,
    )

    file_whitelist = List(
        Unicode(),
        [r".*\.(png|jpg|gif|svg)"],
        config=True,
        help="""Deprecated, use `file_allowlist`""",
    )

    @validate("file_whitelist")
    def _valid_file_whitelist(self, proposal):
        warn(
            "Deprecated, use VoilaConfiguration.file_allowlist instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return proposal["value"]

    file_denylist = List(
        Unicode(),
        [r".*\.(ipynb|py)"],
        config=True,
        help=r"""
        List of regular expressions for controlling which static files are forbidden to be served.
        All files that are served should at least match 1 allowlist rule, and no denylist rule
        Example:
        --VoilaConfiguration.file_allowlist="['.*']" # all files
        --VoilaConfiguration.file_denylist="['private.*', '.*\.(ipynb)']" # except files in the private dir and notebook files
    """,
    )

    file_blacklist = List(
        Unicode(),
        [r".*\.(ipynb|py)"],
        config=True,
        help="""Deprecated, use `file_denylist`""",
    )

    @validate("file_blacklist")
    def _valid_file_blacklist(self, proposal):
        warn(
            "Deprecated, use VoilaConfiguration.file_denylist instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return proposal["value"]

    language_kernel_mapping = Dict(
        {},
        config=True,
        help="""Mapping of language name to kernel name
        Example mapping python to use xeus-python, and C++11 to use xeus-cling:
        --VoilaConfiguration.extension_language_mapping='{"python": "xpython", "C++11": "xcpp11"}'
        """,
    )

    extension_language_mapping = Dict(
        {},
        config=True,
        help="""Mapping of file extension to kernel language
        Example mapping .py files to a python language kernel, and .cpp to a C++11 language kernel:
        --VoilaConfiguration.extension_language_mapping='{".py": "python", ".cpp": "C++11"}'
        """,
    )

    http_keep_alive_timeout = Int(
        10,
        config=True,
        help="""
    When a cell takes a long time to execute, the http connection can timeout (possibly because of a proxy).
    Voila sends a 'heartbeat' message after the timeout is passed to keep the http connection alive.
    """,
    )

    show_tracebacks = Bool(
        False,
        config=True,
        help=("Whether to send tracebacks to clients on exceptions."),
    )

    multi_kernel_manager_class = Type(
        config=True,
        default_value="jupyter_server.services.kernels.kernelmanager.AsyncMappingKernelManager",
        # default_value='voila.voila_kernel_manager.VoilaKernelManager',
        klass="jupyter_client.multikernelmanager.MultiKernelManager",
        help="""The kernel manager class. This is useful to specify a different kernel manager,
        for example a kernel manager with support for pooling.
        """,
    )

    kernel_spec_manager_class = Type(
        config=True,
        default_value="jupyter_client.kernelspec.KernelSpecManager",
        klass="jupyter_client.kernelspec.KernelSpecManager",
        help="""The kernel spec manager class.  Allows for setting a custom kernel spec manager for finding and running kernels
        """,
    )

    http_header_envs = List(
        Unicode(),
        [],
        help=r"""
    List of HTTP Headers that should be passed as env vars to the kernel.
    Example: --VoilaConfiguration.http_header_envs="['X-CDSDASHBOARDS-JH-USER']"
    """,
    ).tag(config=True)

    preheat_kernel = Bool(
        False,
        config=True,
        help="""Flag to enable or disable pre-heat kernel option.
        """,
    )
    default_pool_size = Int(
        1,
        config=True,
        help="""Size of pre-heated kernel pool for each notebook. Zero or negative number means disabled.
        """,
    )

    extension_allowlist = List(
        None,
        allow_none=True,
        config=True,
        help="""The list of enabled JupyterLab extensions, if `None`, all extensions are loaded.
        This setting has higher priority than the `extension_denylist`
        """,
    )

    extension_denylist = List(
        None,
        allow_none=True,
        config=True,
        help="""The list of disabled JupyterLab extensions, if `None`, all extensions are loaded""",
    )

    extension_config = Dict(
        None,
        allow_none=True,
        config=True,
        help="""The dictionary of extension configuration, this dict is passed to the frontend
        through the PageConfig""",
    )

    attempt_fix_notebook = Bool(
        True,
        config=True,
        help="""Whether or not voila should attempt to fix and resolve a notebooks kernelspec metadata""",
    )

    prelaunch_hook = Callable(
        default_value=None,
        allow_none=True,
        config=True,
        help="""A function that is called prior to the launch of a new kernel instance
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
            """,
    )

    page_config_hook = Callable(
        default_value=None,
        allow_none=True,
        config=True,
        help="""A function that is called to modify the page config for a given notebook.
            Should be of the form:

            def page_config_hook(
                current_page_config: Dict[str, Any],
                base_url: str,
                settings: Dict[str, Any],
                log: Logger,
                voila_configuration: VoilaConfiguration,
                notebook_path: str
            ) -> Dict[str, Any]:

            The hook receives the default page_config dictionary and all its parameters, it should
            return a dictionary that will be passed to the template as the `page_config` variable
            and the NotebookRenderer. This can be used to pass custom configuration.
            """,
    )

    progressive_rendering = Bool(
        False,
        config=True,
        help="""Flag to enable or disable progressive rendering option.
        This option is not compatible with preheat-kernel option.
        """,
    )

    extra_labextensions_path = List(
        Unicode(),
        config=True,
        help="""Extra paths to look for federated JupyterLab extensions""",
    )
