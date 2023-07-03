#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import asyncio
import json
import os
from pathlib import Path
import sys
import threading
import warnings
from enum import Enum
from functools import partial
from typing import Awaitable, Dict
import site
import websockets
from jupyter_core.paths import jupyter_path
from jupyter_server.utils import url_path_join
from jupyterlab_server.config import get_page_config as gpc
from jupyterlab_server.config import recursive_update
from markupsafe import Markup

from ._version import __version__
from .static_file_handler import TemplateStaticFileHandler


class ENV_VARIABLE(str, Enum):
    VOILA_PREHEAT = "VOILA_PREHEAT"
    VOILA_KERNEL_ID = "VOILA_KERNEL_ID"
    VOILA_BASE_URL = "VOILA_BASE_URL"
    VOILA_SERVER_URL = "VOILA_SERVER_URL"
    VOILA_REQUEST_URL = "VOILA_REQUEST_URL"
    VOILA_APP_IP = "VOILA_APP_IP"
    VOILA_APP_PORT = "VOILA_APP_PORT"
    VOILA_WS_PROTOCOL = "VOILA_WS_PROTOCOL"
    VOILA_WS_BASE_URL = "VOILA_WS_BASE_URL"
    SERVER_NAME = "SERVER_NAME"
    SERVER_PORT = "SERVER_PORT"
    SCRIPT_NAME = "SCRIPT_NAME"
    PATH_INFO = "PATH_INFO"
    QUERY_STRING = "QUERY_STRING"
    SERVER_SOFTWARE = "SERVER_SOFTWARE"
    SERVER_PROTOCOL = "SERVER_PROTOCOL"


def get_server_root_dir(settings):
    # notebook >= 5.0.0 has this in the settings
    if "server_root_dir" in settings:
        return settings["server_root_dir"]

    # This copies the logic added in the notebook in
    #  https://github.com/jupyter/notebook/pull/2234
    contents_manager = settings["contents_manager"]
    root_dir = contents_manager.root_dir
    home = os.path.expanduser("~")
    if root_dir.startswith(home + os.path.sep):
        # collapse $HOME to ~
        root_dir = "~" + root_dir[len(home) :]
    return root_dir


async def _get_request_info(ws_url: str) -> Awaitable:
    try:
        async with websockets.connect(ws_url, open_timeout=5) as websocket:
            ri = await websocket.recv()
    except (TimeoutError, ConnectionRefusedError):
        warnings.warn(f"Failed to connect to {ws_url}")
        return None
    else:
        return ri


def get_page_config(base_url, settings, log):
    page_config = {
        "appVersion": __version__,
        "appUrl": "voila/",
        "themesUrl": "/voila/api/themes",
        "baseUrl": base_url,
        "terminalsAvailable": False,
        "fullStaticUrl": url_path_join(base_url, "voila/static"),
        "fullLabextensionsUrl": url_path_join(base_url, "voila/labextensions"),
    }

    mathjax_config = settings.get("mathjax_config", "TeX-AMS_HTML-full,Safe")
    # TODO Remove CDN usage.
    mathjax_url = settings.get(
        "mathjax_url",
        "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js",
    )
    page_config.setdefault("mathjaxConfig", mathjax_config)
    page_config.setdefault("fullMathjaxUrl", mathjax_url)

    labextensions_path = jupyter_path("labextensions")

    recursive_update(
        page_config,
        gpc(
            labextensions_path,
            logger=log,
        ),
    )
    disabled_extensions = [
        "@voila-dashboards/jupyterlab-preview",
        "@jupyter/collaboration-extension",
    ]
    federated_extensions = page_config["federated_extensions"]
    page_config["federated_extensions"] = [
        x for x in federated_extensions if x["name"] not in disabled_extensions
    ]
    return page_config


def wait_for_request(url: str = None) -> str:
    """Helper function to pause the execution of notebook and wait for
    the pre-heated kernel to be used and all request info is added to
    the environment.

    Args:
        url (str, optional): Address to get request info, if it is not
        provided, `voila` will figure out from the environment variables.
        Defaults to None.

    """
    preheat_mode = os.getenv(ENV_VARIABLE.VOILA_PREHEAT, "False")
    if preheat_mode == "False":
        return

    request_info = None
    if url is None:
        protocol = os.getenv(ENV_VARIABLE.VOILA_WS_PROTOCOL, "ws")
        server_ip = os.getenv(ENV_VARIABLE.VOILA_APP_IP, "127.0.0.1")
        server_port = os.getenv(ENV_VARIABLE.VOILA_APP_PORT, "8866")
        server_url = os.getenv(ENV_VARIABLE.VOILA_SERVER_URL, "/")
        # Use `VOILA_SERVER_URL` if `VOILA_WS_BASE_URL` not specified.
        ws_base_url = os.getenv(ENV_VARIABLE.VOILA_WS_BASE_URL, server_url)
        url = f"{protocol}://{server_ip}:{server_port}{ws_base_url}voila/query"

    kernel_id = os.getenv(ENV_VARIABLE.VOILA_KERNEL_ID)
    ws_url = f"{url}/{kernel_id}"

    def inner():
        nonlocal request_info
        loop = asyncio.new_event_loop()
        request_info = loop.run_until_complete(_get_request_info(ws_url))

    thread = threading.Thread(target=inner)
    try:
        thread.start()
        thread.join()
    except (KeyboardInterrupt, SystemExit):
        asyncio.get_event_loop().stop()

    if request_info is not None:
        for k, v in json.loads(request_info).items():
            os.environ[k] = v


def get_query_string(url: str = None) -> str:
    """Helper function to pause the execution of notebook and wait for
    the query string.
    Args:
        url (str, optional): Address to get user query string, if it is not
        provided, `voila` will figure out from the environment variables.
        Defaults to None.
    Returns: The query string provided by `QueryStringSocketHandler`.
    """

    wait_for_request(url)
    return os.getenv(ENV_VARIABLE.QUERY_STRING)


def make_url(template_name: str, base_url: str, path: str) -> str:
    # similar to static_url, but does not assume the static prefix
    settings = {
        "static_url_prefix": f"{base_url}voila/templates/",
        "static_path": None,  # not used in TemplateStaticFileHandler.get_absolute_path
    }
    return TemplateStaticFileHandler.make_static_url(
        settings, f"{template_name}/{path}"
    )


def include_css(template_name: str, base_url: str, name: str) -> str:
    code = f'<link rel="stylesheet" type="text/css" href="{make_url(template_name, base_url, name)}">'
    return Markup(code)


def include_js(template_name: str, base_url: str, name: str) -> str:
    code = f'<script src="{make_url(template_name, base_url, name)}"></script>'
    return Markup(code)


def include_url(template_name: str, base_url: str, name: str) -> str:
    return Markup(make_url(template_name, base_url, name))


def include_lab_theme(base_url: str, name: str) -> str:
    """Override the function from `nbconvert`"""
    return ""


def create_include_assets_functions(template_name: str, base_url: str) -> Dict:
    return {
        "include_css": partial(include_css, template_name, base_url),
        "include_js": partial(include_js, template_name, base_url),
        "include_url": partial(include_url, template_name, base_url),
        "include_lab_theme": partial(include_lab_theme, base_url),
    }


def pjoin(*args):
    """Join paths to create a real path."""
    return os.path.abspath(os.path.join(*args))


def get_data_dir():
    """Get the Voila data directory."""

    from .app import HERE

    # Use the default locations for data_files.
    app_dir = pjoin(sys.prefix, "share", "jupyter", "voila")

    # Check for a user level install.
    # Ensure that USER_BASE is defined
    if hasattr(site, "getuserbase"):
        site.getuserbase()
    userbase = getattr(site, "USER_BASE", None)
    if HERE.startswith(userbase) and not app_dir.startswith(userbase):
        app_dir = pjoin(userbase, "share", "jupyter", "lab")

    # Check for a system install in '/usr/local/share'.
    elif (
        sys.prefix.startswith("/usr")
        and not os.path.exists(app_dir)
        and os.path.exists("/usr/local/share/jupyter/voila")
    ):
        app_dir = "/usr/local/share/jupyter/voila"

    # We must resolve the path to get the canonical case of the path for
    # case-sensitive systems
    return str(Path(app_dir).resolve())
