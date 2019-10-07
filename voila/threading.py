import asyncio
import concurrent.futures
import inspect
import threading
import tornado.queues

# As long as we support Python35, we use this library to get as async
# generators: https://pypi.org/project/async_generator/
from async_generator import async_generator, yield_


class ThreadedAsyncGenerator(threading.Thread):
    def __init__(self, main_ioloop, fn, *args, **kwargs):
        super(ThreadedAsyncGenerator, self).__init__()
        self.main_ioloop = main_ioloop
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.queue = tornado.queues.Queue()
        self.start()

    def run(self):
        ioloop_in_thread = asyncio.new_event_loop()
        asyncio.set_event_loop(ioloop_in_thread)
        return ioloop_in_thread.run_until_complete(self._run())

    async def _run(self):
        async for item in self.fn(*self.args, **self.kwargs):
            def thread_safe_put(item=item):
                self.queue.put(item)
            self.main_ioloop.call_soon_threadsafe(thread_safe_put)

        def thread_safe_end():
            self.queue.put(StopIteration)
        self.main_ioloop.call_soon_threadsafe(thread_safe_end)

    @async_generator
    async def __aiter__(self):
        while True:
            value = await self.queue.get()
            if value == StopIteration:
                break
            await yield_(value)


def async_generator_to_thread(fn):
    """Calls an async generator function fn in a thread and async returns the results"""
    ioloop = asyncio.get_event_loop()

    def wrapper(*args, **kwargs):
        gen = ThreadedAsyncGenerator(ioloop, fn, *args, **kwargs)
        return gen
    return wrapper
