#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import asyncio
import os
import threading
from enum import Enum
from typing import Awaitable

import websockets


class ENV_VARIABLE(str, Enum):

    VOILA_PREHEAT = 'VOILA_PREHEAT'
    VOILA_KERNEL_ID = 'VOILA_KERNEL_ID'
    VOILA_BASE_URL = 'VOILA_BASE_URL'
    VOILA_APP_IP = 'VOILA_APP_IP'
    VOILA_APP_PORT = 'VOILA_APP_PORT'
    VOILA_APP_PROTOCOL = 'VOILA_APP_PROTOCOL'
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


async def _get_user_query(ws_url: str) -> Awaitable:
    async with websockets.connect(ws_url) as websocket:
        qs = await websocket.recv()
    return qs


def get_user_query(url: str = None) -> str:
    """Helper function to pause the execution of notebook and wait for
    the query string.

    Args:
        url (str, optional): Address to get user query string, if it is not
        provided, `voila` will figure out from the environment variables. Defaults to None.

    Returns: The query string provided by `QueryStringSocketHandler`.
    """

    preheat_mode = os.getenv(ENV_VARIABLE.VOILA_PREHEAT, 'False')
    if preheat_mode == 'False':
        return os.getenv(ENV_VARIABLE.QUERY_STRING)

    query_string = None
    if url is None:
        protocol = os.getenv(ENV_VARIABLE.VOILA_APP_PROTOCOL, 'ws')
        server_ip = os.getenv(ENV_VARIABLE.VOILA_APP_IP, '127.0.0.1')
        server_port = os.getenv(ENV_VARIABLE.VOILA_APP_PORT, '8866')
        base_url = os.getenv(ENV_VARIABLE.VOILA_BASE_URL, '/')
        url = f'{protocol}://{server_ip}:{server_port}{base_url}voila/query'

    kernel_id = os.getenv(ENV_VARIABLE.VOILA_KERNEL_ID)
    ws_url = f'{url}/{kernel_id}'

    def inner():
        nonlocal query_string
        loop = asyncio.new_event_loop()
        query_string = loop.run_until_complete(_get_user_query(ws_url))

    thread = threading.Thread(target=inner)
    try:
        thread.start()
        thread.join()
    except (KeyboardInterrupt, SystemExit):
        asyncio.get_event_loop().stop()

    return query_string
