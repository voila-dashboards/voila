#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

from jupyter_server.utils import url_path_join

def add_base_url_to_handlers(base_url, handlers):
    """Adds the base_url in front of the urls in the Tornado handlers"""
    return [tuple([url_path_join(base_url, url)] + list(tail)) for url, *tail in handlers]