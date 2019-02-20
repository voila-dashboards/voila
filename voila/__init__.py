#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################


def _jupyter_nbextension_paths():
    return [dict(
        section="notebook",
        src="static",
        dest="voila",
        require="voila/nbextension")]
