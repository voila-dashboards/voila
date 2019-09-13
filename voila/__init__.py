#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

from ._version import __version__  # noqa
from .app import Voila  # noqa

load_jupyter_server_extension = Voila.load_jupyter_server_extension


def _jupyter_nbextension_paths():
    return [dict(
        section="notebook",
        src="static",
        dest="voila",
        require="voila/extension")]
