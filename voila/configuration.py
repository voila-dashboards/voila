#############################################################################
# Copyright (c) 2018, QuantStack                                            #
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import traitlets.config
from traitlets import Unicode, Bool, Dict, List, Int


class VoilaConfiguration(traitlets.config.Configurable):
    """Common configuration options between the server extension and the application."""
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
    enable_nbextensions = Bool(False, config=True, help=('Set to True for Voila to load notebook extensions'))

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
        Example mapping python to use xeus-python, and C++11 to use xeus-cling:
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
