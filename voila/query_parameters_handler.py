from tornado.websocket import WebSocketHandler
import logging


class QueryStringSocketHandler(WebSocketHandler):
    waiters = dict()
    cache = dict()

    def open(self, kernel_id):
        QueryStringSocketHandler.waiters[kernel_id] = self
        if kernel_id in self.cache:
            self.write_message(self.cache[kernel_id])

    def on_close(self):
        for k_id, waiter in QueryStringSocketHandler.waiters.items():
            if waiter == self:
                break
        del QueryStringSocketHandler.waiters[k_id]

    @classmethod
    def send_updates(cls, msg):
        kernel_id = msg['kernel_id']
        payload = msg['payload']
        waiter = cls.waiters.get(kernel_id, None)
        if waiter is not None:
            try:
                waiter.write_message(payload)
            except Exception:
                logging.error("Error sending message", exc_info=True)
        else:
            cls.cache[kernel_id] = payload
