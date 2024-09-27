import json
from typing import Awaitable
from jupyter_server.base.handlers import JupyterHandler
from tornado.websocket import WebSocketHandler
from jupyter_server.base.websocket import WebSocketMixin
from jupyter_core.utils import ensure_async
from nbclient.exceptions import CellExecutionError
from voila.execute import VoilaExecutor, strip_code_cell_warnings
import nbformat
import traceback
import sys


class ExecutionRequestHandler(WebSocketMixin, WebSocketHandler, JupyterHandler):
    _kernels = {}
    _execution_data = {}
    _cache = {}

    def initialize(self, **kwargs):
        super().initialize()

    def open(self, kernel_id: str) -> None:
        """Create a new websocket connection, this connection is
        identified by the kernel id.

        Args:
            kernel_id (str): Kernel id used by the notebook when it opens
            the websocket connection.
        """
        super().open()
        self._kernel_id = kernel_id
        ExecutionRequestHandler._kernels[kernel_id] = self
        self.write_message({"action": "initialized", "payload": {}})
        if kernel_id in self._cache:
            self.write_message(self._cache[kernel_id])

    async def on_message(self, message_str: str | bytes) -> Awaitable[None] | None:
        message = json.loads(message_str)
        action = message.get("action", None)
        payload = message.get("payload", {})
        if action == "execute":
            request_kernel_id = payload.get("kernel_id")

            kernel_future = self.kernel_manager.get_kernel(self._kernel_id)
            km = await ensure_async(kernel_future)
            execution_data = self._execution_data.get(self._kernel_id)

            nb = execution_data["nb"]
            self._executor = executor = VoilaExecutor(
                nb,
                km=km,
                config=execution_data["config"],
                show_tracebacks=execution_data["show_tracebacks"],
            )
            executor.kc = await executor.async_start_new_kernel_client()

            for cell_idx, input_cell in enumerate(nb.cells):
                try:
                    output_cell = await executor.execute_cell(
                        input_cell, None, cell_idx, store_history=False
                    )
                except TimeoutError:
                    output_cell = input_cell

                except CellExecutionError:
                    self.log.exception(
                        "Error at server while executing cell: %r", input_cell
                    )
                    if executor.should_strip_error():
                        strip_code_cell_warnings(input_cell)
                        executor.strip_code_cell_errors(input_cell)
                    output_cell = input_cell

                except Exception as e:
                    self.log.exception(
                        "Error at server while executing cell: %r", input_cell
                    )
                    output_cell = nbformat.v4.new_code_cell()
                    if executor.should_strip_error():
                        output_cell.outputs = [
                            {
                                "output_type": "stream",
                                "name": "stderr",
                                "text": "An exception occurred at the server (not the notebook). {}".format(
                                    executor.cell_error_instruction
                                ),
                            }
                        ]
                    else:
                        output_cell.outputs = [
                            {
                                "output_type": "error",
                                "ename": type(e).__name__,
                                "evalue": str(e),
                                "traceback": traceback.format_exception(
                                    *sys.exc_info()
                                ),
                            }
                        ]
                finally:
                    await self.write_message(
                        {
                            "action": "execution_result",
                            "payload": {
                                "request_kernel_id": request_kernel_id,
                                "output_cell": output_cell,
                                "cell_index": cell_idx,
                            },
                        }
                    )

    def on_close(self) -> None:
        if self._executor:
            del self._executor.kc
