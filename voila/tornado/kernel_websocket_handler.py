import json
from typing import Any, Dict, Optional, Union

try:
    from jupyter_server.services.kernels.websocket import (
        KernelWebsocketHandler as WebsocketHandler,
    )
    from jupyter_server.services.kernels.connection.base import (
        deserialize_msg_from_ws_v1,
        serialize_msg_to_ws_v1,
    )

    JUPYTER_SERVER_2 = True
except ImportError:
    from jupyter_server.services.kernels.handlers import (
        ZMQChannelsHandler as WebsocketHandler,
    )

    JUPYTER_SERVER_2 = False


def read_header_from_binary_message(ws_msg: bytes) -> Optional[Dict]:
    """Read message header using the v1 protocol."""

    offset_number = int.from_bytes(ws_msg[:8], "little")
    offsets = [
        int.from_bytes(ws_msg[8 * (i + 1) : 8 * (i + 2)], "little")
        for i in range(offset_number)
    ]
    try:
        header = ws_msg[offsets[1] : offsets[2]].decode("utf-8")
        return json.loads(header)
    except Exception:
        return


if JUPYTER_SERVER_2:
    SUPPORTED_SUBPROTOCOL = ["v1.kernel.websocket.jupyter.org"]

    class VoilaKernelWebsocketHandler(WebsocketHandler):

        _ALL_EXECUTION_DATA = {}

        def execution_data(self) -> Dict[str, Any]:
            return self._ALL_EXECUTION_DATA.get(self.kernel_id, None)

        def _get_message_content(self, ws_msg):

            connection = self.connection
            channel, msg_list = deserialize_msg_from_ws_v1(ws_msg)
            msg = {"header": None, "content": None}

            msg_header = connection.get_part("header", msg["header"], msg_list)
            msg_content = connection.get_part("content", msg["content"], msg_list)

            return {
                "header": msg_header,
                "content": msg_content,
                "channel": channel,
                "msg_list": msg_list,
            }

        def on_message(self, ws_msg):
            """
            This is an adaptation of the `handle_incoming_message` method of
            `ZMQChannelsWebsocketConnection` to replace cell index with the
            real cell code.
            """
            connection = self.connection
            subprotocol = connection.subprotocol
            if not connection.channels:
                # already closed, ignore the message
                connection.log.debug("Received message on closed websocket %r", ws_msg)
                return
            if subprotocol not in SUPPORTED_SUBPROTOCOL:
                # Never happen in Voila case
                return

            channel, msg_list = deserialize_msg_from_ws_v1(ws_msg)
            msg = {"header": None, "content": None}

            if channel is None:
                connection.log.warning("No channel specified, assuming shell: %s", msg)
                channel = "shell"
            if channel not in connection.channels:
                connection.log.warning("No such channel: %r", channel)
                return
            am = connection.multi_kernel_manager.allowed_message_types
            ignore_msg = False
            msg_header = connection.get_part("header", msg["header"], msg_list)
            msg_content = connection.get_part("content", msg["content"], msg_list)
            if msg_header["msg_type"] == "execute_request":
                execution_data = self.execution_data()
                cells = execution_data["cells"]
                code = msg_content.get("code")
                try:
                    cell_idx = int(code)
                    cell = cells[cell_idx]
                    if cell["cell_type"] != "code":
                        cell["source"] = ""
                    msg_content["code"] = cell["source"]
                    msg_list[3] = connection.session.pack(msg_content)

                except Exception:
                    connection.log.warning("Unsupported code cell %s" % code)

            if am:
                msg["header"] = connection.get_part("header", msg["header"], msg_list)
                assert msg["header"] is not None
                if msg["header"]["msg_type"] not in am:  # type:ignore[unreachable]
                    connection.log.warning(
                        'Received message of type "%s", which is not allowed. Ignoring.'
                        % msg["header"]["msg_type"]
                    )
                    ignore_msg = True
            if not ignore_msg:
                stream = connection.channels[channel]
                connection.session.send_raw(stream, msg_list)

        def write_message(
            self, message: Union[bytes, Dict[str, Any]], binary: bool = False
        ):
            connection = self.connection
            if isinstance(message, bytes):
                header = read_header_from_binary_message(message)
            elif isinstance(message, dict):
                header = message.get("header", None)
            else:
                header = None

            if header:
                msg_type = header.get("msg_type", None)
                if msg_type == "execute_input":
                    return  # Ignore execute_input message
                if msg_type == "error":
                    execution_data = self.execution_data()
                    show_tracebacks = execution_data["show_tracebacks"]
                    if show_tracebacks:
                        return super().write_message(message, binary)
                    data = self._get_message_content(message)
                    content = data.get("content", None)
                    msg_list = data.get("msg_list", None)
                    channel = data.get("channel", None)

                    if content:
                        content["traceback"] = [
                            "There was an error when executing this cell. Please run Voilà with --show_tracebacks=True or --debug to see the error message, or configure VoilaConfiguration.show_tracebacks."
                        ]

                        if msg_list and channel:
                            msg_list[3] = connection.session.pack(content)
                            new_message = serialize_msg_to_ws_v1(msg_list, channel)

                            return super().write_message(new_message, binary)
                        else:
                            return
            return super().write_message(message, binary)

else:
    # Jupyter server 1, only mask the execute input request.
    class VoilaKernelWebsocketHandler(WebsocketHandler):
        def write_message(
            self, message: Union[bytes, Dict[str, Any]], binary: bool = False
        ):
            if isinstance(message, bytes):
                header = read_header_from_binary_message(message)
            elif isinstance(message, dict):
                header = message.get("header", None)
            else:
                header = None

            if header and header.get("msg_type", None) == "execute_input":
                return  # Ignore execute_input message

            return super().write_message(message, binary)
