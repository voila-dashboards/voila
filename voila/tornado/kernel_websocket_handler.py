import json
from typing import Any, Dict, Optional, Union

try:
    from jupyter_server.services.kernels.websocket import KernelWebsocketHandler as WebsocketHandler
except ImportError:
    from jupyter_server.services.kernels.handlers import ZMQChannelsHandler as WebsocketHandler



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
