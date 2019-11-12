import asyncio
import threading
import time
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


def async_execute_in_current_thread(coroutine_function):
    """Decorator which executes coroutine_function in the main thread, but invokable from any other thread as coroutine function"""
    main_ioloop = asyncio.get_event_loop()
    # Tornado queues can be created from a different thrad
    request_queue = tornado.queues.Queue()  # will be used to put the unknown ioloop in (from the other thread)
    result_queue = tornado.queues.Queue()  # will be used to put the result of the function call in

    async def main_thread_task():
        # we call the function directly
        result = await coroutine_function()
        # we then wait till some thread wants the result
        thread_ioloop = await request_queue.get()

        def thread_safe_put(result=result):
            result_queue.put(result)
        # and savely put it on the result_queue (which is why we need the thread's ioloop)
        thread_ioloop.call_soon_threadsafe(thread_safe_put)
    # we launch the task directly, which will wait for the thread
    main_ioloop.create_task(main_thread_task())

    async def wrapper_called_from_thread():
        ioloop = asyncio.get_event_loop()

        def thread_safe_put(thread_ioloop=ioloop):
            request_queue.put(thread_ioloop)
        main_ioloop.call_soon_threadsafe(thread_safe_put)
        result = await result_queue.get()
        return result
    return wrapper_called_from_thread


def busy_wait_execute_in_current_thread(coroutine_function):
    """Decorator which executes coroutine_function in the main thread, but invokable from any other thread as a plain function"""
    main_ioloop = asyncio.get_event_loop()
    result = None

    async def main_thread_task():
        nonlocal result
        # we call the function before we are asked
        result = await coroutine_function()
    # we launch the task directly
    main_ioloop.create_task(main_thread_task())

    def wrapper_called_from_thread():
        # due to Python35 support we cannot ma
        nonlocal result
        while result is None:
            time.sleep(0.05)
        return result
    return wrapper_called_from_thread
