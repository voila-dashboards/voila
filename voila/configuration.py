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
    reveal_theme = Unicode(
        'simple',
        allow_none=True,
        help="""
        Used only with template reveal, ignored otherwise.
        Name of the reveal.js theme to use.
        We look for a file with this name under
        ``reveal_url_prefix``/css/theme/``reveal_theme``.css.
        https://github.com/hakimel/reveal.js/tree/master/css/theme has
        list of themes that ship by default with reveal.js.
        """
    ).tag(config=True)
    reveal_transition = Unicode(
        'slide',
        allow_none=True,
        help="""
        Used only with template reveal, ignored otherwise.
        Name of the reveal.js transition to use.
        The list of transitions that ships by default with reveal.js are:
        none, fade, slide, convex, concave and zoom.
        """
    ).tag(config=True)
    reveal_scroll = Bool(
        False,
        allow_none=True,
        help="""
        Used only with template reveal, ignored otherwise.
        If True, enable scrolling within each slide
        """
    ).tag(config=True)
    theme = Unicode('light').tag(config=True)
    strip_sources = Bool(True, help='Strip sources from rendered html').tag(config=True)
    enable_nbextensions = Bool(False, config=True, help=('Set to True for Voila to load notebook extensions'))
