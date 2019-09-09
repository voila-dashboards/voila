import asyncio

import tornado.gen

from .execute import CellExecutor, executenb
from .threading import ThreadExecutor

# As long as we support Python35, we use this library to get as async
# generators: https://pypi.org/project/async_generator/
from async_generator import async_generator, yield_


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

    @async_generator
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
            await yield_(cell)
