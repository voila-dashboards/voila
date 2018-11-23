#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os
from pathlib import Path
from jupyter_server import DEFAULT_STATIC_FILES_PATH, DEFAULT_TEMPLATE_PATH_LIST


STATIC_ROOT = DEFAULT_STATIC_FILES_PATH

TEMPLATE_ROOT = DEFAULT_TEMPLATE_PATH_LIST[-1]

NBCONVERT_TEMPLATE_ROOT = Path(os.path.dirname(__file__)) / 'nbconvert_templates'
