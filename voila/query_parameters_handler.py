from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler
import logging


class QueryParametersHandler(RequestHandler):

    def initialize(self, kernel_manager=None):
        self._kernel_manager = None
        if hasattr(kernel_manager, 'get_query_params'):
            self._kernel_manager = kernel_manager

    async def get(self, kernel_id: str, var_name: str):
        if self._kernel_manager is not None:
            content = self._kernel_manager.get_query_params(kernel_id, var_name)
            self.finish(content[0])
        else:
            self.finish(None)


class QueryStringSocketHandler(WebSocketHandler):
    waiters = dict()
    cache = dict()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self, kernel_id):
        print("open connection to", kernel_id)
        QueryStringSocketHandler.waiters[kernel_id] = self
        if kernel_id in self.cache:
            print('sending', self.cache[kernel_id])
            self.write_message(self.cache[kernel_id])

    def on_close(self):
        for k_id, waiter in QueryStringSocketHandler.waiters.items():
            if waiter == self:
                break
        print('closing', k_id)
        del QueryStringSocketHandler.waiters[k_id]

    @classmethod
    def send_updates(cls, msg):
        kernel_id = msg['kernel_id']
        payload = msg['payload']
        print("sending message to %d waiters", kernel_id)
        waiter = cls.waiters.get(kernel_id, None)
        if waiter is not None:
            try:
                waiter.write_message(payload)
            except Exception:
                logging.error("Error sending message", exc_info=True)
        else:
            cls.cache[kernel_id] = payload