#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import traitlets.config
from traitlets import Unicode, Bool


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
    theme = Unicode('light').tag(config=True)
    strip_sources = Bool(True, help='Strip sources from rendered html').tag(config=True)
