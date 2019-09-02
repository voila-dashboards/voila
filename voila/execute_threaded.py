import asyncio
import concurrent.futures
import inspect

import tornado.gen
from jupyter_client import KernelManager

from .execute import CellExecutor, executenb


class ThreadExecutor(concurrent.futures.ThreadPoolExecutor):
    """Executor that executes on a single thread and uses coroutines

    We assume that if two jobs are submitted, they are executed in the same
    order. This is important for executing cells in order.  The implementatioån
    of ThreadPoolExecutor works this way by using a Queue.
    """
    def __init__(self):
        super(ThreadExecutor, self).__init__(max_workers=1)

    def submit(self, fn, *args, **kwargs):
        """This submit allows fn to also be a coroutine, which will be awaited for"""
        def coroutine_wrapper(*args, **kwargs):
            try:
                ioloop_in_thread = asyncio.get_event_loop()
            except RuntimeError:
                ioloop_in_thread = None
            if ioloop_in_thread is None:
                ioloop_in_thread = asyncio.new_event_loop()
                asyncio.set_event_loop(ioloop_in_thread)
            return ioloop_in_thread.run_until_complete(fn(*args, **kwargs))
        if inspect.iscoroutinefunction(fn):
            return super(ThreadExecutor, self).submit(coroutine_wrapper, *args, **kwargs)
        else:
            return super(ThreadExecutor, self).submit(fn, *args, **kwargs)

    async def submit_async(self, fn, *args, **kwargs):
        """A coroutine version of submit, since an asyncio Future is not a concurrent.future.Future

        Allow for the following:
        >>> import asyncio
        >>> await executor.submit_async(asyncio.sleep, 1)
        """
        ioloop = asyncio.get_event_loop()
        return await ioloop.run_in_executor(self, fn, *args, **kwargs)


class CellExecutorThreaded(CellExecutor):
    """Executes the notebook cells in a thread.

    For the network/zmq layer it is important that all calls are done from the
    same thread, which is the reason we use a single thread.

    """
    def __init__(self, notebook, cwd, multi_kernel_manager):
        self.notebook = notebook
        self.cwd = cwd
        self.multi_kernel_manager = multi_kernel_manager
        self.kernel_started = False
        self.executor = ThreadExecutor()

    def notebook_execute(self, nb, kernel_id):
        return None

    async def kernel_start(self):
        assert not self.kernel_started, "kernel was already started"

        async def start_kernel_in_thread():
            # Launch kernel
            self.kernel_started = True
            km = self.multi_kernel_manager.get_kernel(self.kernel_id)
            self.client = km.client()
            self.client.start_channels()
            startup_timeout = 10
            self.client.wait_for_ready(timeout=startup_timeout)
            self.kernel_started = True
            return self.kernel_id
        # It seems we cannot start the kernel in the thread, it might because
        # the control channel is already started, and the jupyter_server part
        # will fail (we get a pending status of the websocket at the client). We
        # can get an additional performance increase if we do this in the thread
        # as well.
        self.kernel_id = await tornado.gen.maybe_future(self.multi_kernel_manager.start_kernel(kernel_name=self.notebook.metadata.kernelspec.name, path=self.cwd))
        return await self.executor.submit_async(start_kernel_in_thread)

    async def cell_generator(self, nb, kernel_id):
        km = self.multi_kernel_manager.get_kernel(kernel_id)

        def cell_execute(i):
            all_cells = list(nb.cells)  # copy the cells, since we will modify in place
            # we execute one cell at a time
            nb.cells = [all_cells[i]]  # reuse the same notebook
            result = executenb(nb, km=km, cwd=self.cwd)  # , config=self.traitlet_config)
            cell = result.cells[0]  # keep a reference to the executed cell
            nb.cells = all_cells  # restore notebook in case we access it from the template
            # we don't filter empty cells, since we do not know how many empty code cells we will have
            return cell

        ioloop = asyncio.get_event_loop()
        N = len(self.notebook.cells)
        cell_futures = [ioloop.run_in_executor(self.executor, cell_execute, i) for i in range(N)]
        for cell_future in cell_futures:
            cell = await cell_future
            yield cell
