#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os
from pathlib import Path

ROOT = Path(os.path.dirname(__file__))
STATIC_ROOT = ROOT / 'static'
TEMPLATE_ROOT = ROOT / 'templates'

