#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os
import websockets
from typing import Awaitable
from enum import Enum


class ENV_VARIABLE(str, Enum):

    VOILA_PREHEAT = 'VOILA_PREHEAT'
    VOILA_KERNEL_ID = 'VOILA_KERNEL_ID'
    VOILA_BASE_URL = 'VOILA_BASE_URL'
    VOILA_APP_IP = 'VOILA_APP_IP'
    VOILA_APP_PORT = 'VOILA_APP_PORT'
    SERVER_NAME = 'SERVER_NAME'
    SERVER_PORT = 'SERVER_PORT'
    SCRIPT_NAME = 'SCRIPT_NAME'
    PATH_INFO = 'PATH_INFO'
    QUERY_STRING = 'QUERY_STRING'
    SERVER_SOFTWARE = 'SERVER_SOFTWARE'
    SERVER_PROTOCOL = 'SERVER_PROTOCOL'


def get_server_root_dir(settings):
    # notebook >= 5.0.0 has this in the settings
    if 'server_root_dir' in settings:
        return settings['server_root_dir']

    # This copies the logic added in the notebook in
    #  https://github.com/jupyter/notebook/pull/2234
    contents_manager = settings['contents_manager']
    root_dir = contents_manager.root_dir
    home = os.path.expanduser('~')
    if root_dir.startswith(home + os.path.sep):
        # collapse $HOME to ~
        root_dir = '~' + root_dir[len(home):]
    return root_dir


async def get_user_query(url: str = None) -> Awaitable:
    """Helper function to pause the execution of notebook and wait for
    the query string.

    Args:
        url (str, optional): Address to get user query string, if it is not
        provided, `voila` will figure out from the environment variables. Defaults to None.

    Returns:
        Awaitable: The query string provided by `QueryStringSocketHandler`.
    """
    if url is None:
        base_url = os.getenv(ENV_VARIABLE.VOILA_BASE_URL, '/')
        server_ip = os.getenv(ENV_VARIABLE.VOILA_APP_IP, '127.0.0.1')
        server_port = os.getenv(ENV_VARIABLE.VOILA_APP_PORT, '8866')
        url = f'ws://{server_ip}:{server_port}{base_url}voila/query'

    preheat_mode = os.getenv(ENV_VARIABLE.VOILA_PREHEAT, 'False')
    kernel_id = os.getenv(ENV_VARIABLE.VOILA_KERNEL_ID)
    ws_url = f'{url}/{kernel_id}'

    if preheat_mode == 'True':
        async with websockets.connect(ws_url) as websocket:
            qs = await websocket.recv()
    else:
        qs = os.getenv(ENV_VARIABLE.QUERY_STRING)
    return qs
