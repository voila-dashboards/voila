#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import hashlib

from traitlets import Unicode, Union, Type
from pygments.style import Style
from jupyterlab_pygments import JupyterStyle

from nbconvert.preprocessors.base import Preprocessor

try:
    from notebook import DEFAULT_STATIC_FILES_PATH
except ImportError:
    DEFAULT_STATIC_FILES_PATH = None


class VoilaCSSPreprocessor(Preprocessor):
    """
    Preprocessor used to pre-process notebook for HTML output.  Adds IPython notebook
    front-end CSS and Pygments CSS to HTML output.
    """
    highlight_class = Unicode('.highlight',
                              help="CSS highlight class identifier").tag(config=True)

    style = Union([Unicode('default'), Type(klass=Style)],
                  help='Name of the pygments style to use',
                  default_value=JupyterStyle).tag(config=True)

    def __init__(self, *pargs, **kwargs):
        Preprocessor.__init__(self, *pargs, **kwargs)
        self._default_css_hash = None

    def preprocess(self, nb, resources):
        """Fetch and add CSS to the resource dictionary

        Fetch CSS from IPython and Pygments to add at the beginning
        of the html files.  Add this css in resources in the
        "inlining.css" key

        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        """
        resources['inlining'] = {}
        resources['inlining']['css'] = self._generate_header(resources)
        return nb, resources

    def _generate_header(self, resources):
        """
        Fills self.header with lines of CSS extracted from IPython
        and Pygments.
        """
        header = []

        # Add pygments CSS

        from pygments.formatters import HtmlFormatter
        formatter = HtmlFormatter(style=self.style)
        pygments_css = formatter.get_style_defs(self.highlight_class)
        header.append(pygments_css)

        return header

    def _hash(self, filename):
        """Compute the hash of a file."""
        md5 = hashlib.md5()
        with open(filename, 'rb') as f:
            md5.update(f.read())
        return md5.digest()
