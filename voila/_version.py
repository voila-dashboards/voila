#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import re

# Version string must appear intact for tbump versioning
__version__ = '0.2.11'

# Build up version_info tuple for backwards compatibility
pattern = r'(?P<major>\d+).(?P<minor>\d+).(?P<patch>\d+)(?P<rest>.*)'
match = re.match(pattern, __version__)
parts = [int(match[part]) for part in ['major', 'minor', 'patch']]
if match['rest']:
    parts.append(match['rest'])
version_info = tuple(parts)
