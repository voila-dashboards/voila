#############################################################################
# Copyright (c) 2018, QuantStack                                            #
# Copyright (c) 2018, Voilà Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import traitlets.config
from traitlets import Unicode, Bool, Dict, List, Int, Enum


class VoilaConfiguration(traitlets.config.Configurable):
    """Common configuration options between the server extension and the application."""
    allow_template_override = Enum(['YES', 'NOTEBOOK', 'NO'], 'YES', help='''
    Allow overriding the template (YES), or not (NO), or only from the notebook metadata.
    ''').tag(config=True)
    allow_theme_override = Enum(['YES', 'NOTEBOOK', 'NO'], 'YES', help='''
    Allow overriding the theme (YES), or not (NO), or only from the notebook metadata.
    ''').tag(config=True)
    template = Unicode(
        'lab',
        config=True,
        allow_none=True,
        help=(
            'template name to be used by voila.'
        )
    )
    resources = Dict(
        allow_none=True,
        help="""
        extra resources used by templates;
        example use with --template=reveal
        --VoilaConfiguration.resources="{'reveal': {'transition': 'fade', 'scroll': True}}"
        """
    ).tag(config=True)
    theme = Unicode('light').tag(config=True)
    strip_sources = Bool(True, help='Strip sources from rendered html').tag(config=True)
    enable_nbextensions = Bool(False, config=True, help=('Set to True for Voilà to load notebook extensions'))

    file_whitelist = List(
        Unicode(),
        [r'.*\.(png|jpg|gif|svg)'],
        help=r"""
    List of regular expressions for controlling which static files are served.
    All files that are served should at least match 1 whitelist rule, and no blacklist rule
    Example: --VoilaConfiguration.file_whitelist="['.*\.(png|jpg|gif|svg)', 'public.*']"
    """,
    ).tag(config=True)

    file_blacklist = List(
        Unicode(),
        [r'.*\.(ipynb|py)'],
        help=r"""
    List of regular expressions for controlling which static files are forbidden to be served.
    All files that are served should at least match 1 whitelist rule, and no blacklist rule
    Example:
    --VoilaConfiguration.file_whitelist="['.*']" # all files
    --VoilaConfiguration.file_blacklist="['private.*', '.*\.(ipynb)']" # except files in the private dir and notebook files
    """
    ).tag(config=True)

    language_kernel_mapping = Dict(
        {},
        help="""Mapping of language name to kernel name
        Example mapping python to use xeus-pythoRen, and C++11 to use xeus-cling:
        --VoilaConfiguration.extension_language_mapping='{"python": "xpython", "C++11": "xcpp11"}'
        """,
    ).tag(config=True)

    extension_language_mapping = Dict(
        {},
        help='''Mapping of file extension to kernel language
        Example mapping .py files to a python language kernel, and .cpp to a C++11 language kernel:
        --VoilaConfiguration.extension_language_mapping='{".py": "python", ".cpp": "C++11"}'
        ''',
    ).tag(config=True)

    http_keep_alive_timeout = Int(10, help="""
    When a cell takes a long time to execute, the http connection can timeout (possibly because of a proxy).
    Voila sends a 'heartbeat' message after the timeout is passed to keep the http connection alive.
    """).tag(config=True)

    warm_kernel = Bool(default_value=False,
                       help="""Kernel warming starts instances of the kernel prior to a user
                       visiting the website to request one. The goal of this is to reduce the
                       response time.

                       This variable has several dependent variables:

                       `warm_kernel_preload_count` (int); This variable controls how many kernel instances are staged. This
                       is useful if you generally have users visiting in bursts, as several kernels
                       will be warmed together.

                       `warm_kernel_preexecute_cell_count` (int); This variable allows and controls the preexecution of cells
                       after kernel startup, e.g. after starting a kernel, execute the first 2 cells of imports prior to a user
                       visiting the page. This can dramatically reduce startup time, but since some code might condition on the
                       user visiting the site or have other execution side effects, one should exercise caution.

                       Note: Kernel warming is only available when you run Voilà against a specific notebook (since notebooks
                       might have different kernels).
                       """)

    warm_kernel_preload_count = Int(default_value=1,
                                    help="""This variable controls how many kernel instances are staged. This
                                    is useful if you generally have users visiting in bursts, as several kernels
                                    will be warmed together.""")

    warm_kernel_preexecute_cell_count = Int(default_value=1,
                                            help="""This variable allows and controls the preexecution of cells
                                            after kernel startup, e.g. after starting a kernel, execute the first 2 cells of imports prior to a user
                                            visiting the page. This can dramatically reduce startup time, but since some code might condition on the
                                            user visiting the site or have other execution side effects, one should exercise caution.""")
