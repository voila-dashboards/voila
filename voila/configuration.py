#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import traitlets.config
from traitlets import Unicode, Bool, Dict


class VoilaConfiguration(traitlets.config.Configurable):
    """Common configuration options between the server extension and the application."""
    template = Unicode(
        'default',
        config=True,
        allow_none=True,
        help=(
            'template name to be used by voila.'
        )
    )
    extra_resources = Dict(
        {},
        allow_none=True,
        help="""
        extra resources used by templates;
        example use with --template=reveal
        --extra_resources="{'reveal': {'transition': 'fade', 'scroll': True}}"
        """
    ).tag(config=True)
    theme = Unicode('light').tag(config=True)
    strip_sources = Bool(True, help='Strip sources from rendered html').tag(config=True)
    enable_nbextensions = Bool(False, config=True, help=('Set to True for Voila to load notebook extensions'))
