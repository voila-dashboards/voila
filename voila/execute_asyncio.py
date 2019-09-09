import argparse
import asyncio
import collections
import logging
import os
import sys

import nbformat
import zmq.asyncio
import tornado.gen
from jupyter_client import KernelManager

from .execute import CellExecutor

# As long as we support Python35, we use this library to get as async
# generators: https://pypi.org/project/async_generator/
from async_generator import async_generator, yield_


class CellExecutorAsyncio(CellExecutor):
    def __init__(self, notebook, cwd, multi_kernel_manager=None):
        self.notebook = notebook
        self.cwd = cwd
        self.multi_kernel_manager = multi_kernel_manager
        self.client = None
        self.current_msg_id = None
        self.cell_index = None
        self.startup_timeout = 4
        self.idle_future = collections.defaultdict(asyncio.Future)
        self.started_io = asyncio.Future()
        self.started_shell = asyncio.Future()
        self.kernel_manager = KernelManager(
            client_class='jupyter_client.asyncio.client.AsyncioKernelClient',
            kernel_name=self.notebook.metadata.kernelspec.name,
            context=zmq.asyncio.Context.instance()
            )

    async def start_test_kernel(self):
        from jupyter_client.asyncio.client import AsyncioKernelClient
        self.client = AsyncioKernelClient()
        self.client.log.setLevel('DEBUG')
        self.client.load_connection_file('/Users/maartenbreddels/Library/Jupyter/runtime/conn.json')
        self.client.start_channels_async()
        asyncio.ensure_future(self._handle_io())
        asyncio.ensure_future(self._handle_shell())
        await self.started_io
        await self.started_shell
        self.log.debug('started channels')
        msg = self.client.session.msg('kernel_info_request')
        msg_id = msg['header']['msg_id']
        await self.client.shell_channel.send(msg)
        self.log.debug('wait for idle: %r', msg_id)
        self.log.debug('done with idle: %r', await self.idle_future[msg_id])
        # await self.client.wait_for_ready_async(timeout=self.startup_timeout)
        # return r

    async def kernel_start(self):
        kernel_id = None  # in case we don't have a multi_kernel_manager
        if self.multi_kernel_manager is not None:
            # We start the kernel using the multi_kernel_manager, this will give
            # us a kernel_id that is used at the front-end to specificy which
            # kernel we are using.
            kernel_id = await tornado.gen.maybe_future(self.multi_kernel_manager.start_kernel(kernel_name=self.notebook.metadata.kernelspec.name, path=self.cwd))
            kernel_manager = self.multi_kernel_manager.get_kernel(kernel_id)
            self.kernel_manager.load_connection_info(kernel_manager.get_connection_info())
        else:
            # Otherwise we just start a kernel manager
            self.kernel_manager.start_kernel()
        # TODO: we may want to connect and shutdown in the execute_cell generator instead
        self.client = self.kernel_manager.client()
        self.kernel_started = True
        self.log.debug('starting channels...')
        self.client.start_channels_async()
        self.log.debug('started channels!')
        msg = self.client.session.msg('kernel_info_request')
        await self.client.shell_channel.send(msg)
        await self.client.wait_for_ready_async()
        asyncio.ensure_future(self._handle_io())
        asyncio.ensure_future(self._handle_shell())
        await self.started_io
        await self.started_shell
        return kernel_id

    async def _handle_shell(self):
        self.started_shell.set_result(None)
        while True:
            try:
                msg = await self.client.shell_channel.get_msg(True)
                msg_id = msg['parent_header'].get('msg_id', 'dummy')
                self.log.debug('shell msg: %r: %r', msg_id, msg)
                # msg_type = msg['msg_type']
                # content = msg['content']
            except Exception:
                self.log.exception('issue with handling the shell channel')
            # if msg_type == 'kernel_info_reply':
            #     print('set None future')
            #     self.idle_future[None].set_result(msg_id)

    async def _handle_io(self):
        self.started_io.set_result(None)
        while True:
            try:
                msg = await self.client.iopub_channel.get_msg(True)
                msg_type = msg['msg_type']
                msg_id = msg['parent_header'].get('msg_id', 'dummy')
                content = msg['content']
                if msg_type == 'status':
                    if content['execution_state'] == 'idle':
                        self.log.debug('idle for: %s', msg_id)
                        self.idle_future[msg_id].set_result(msg_id)
                self.log.debug('io msg: %r: %r', msg_id, msg)
                # if msg_id == self.current_msg_id:
                self.process_io(msg)
            except Exception:
                self.log.exception('issue with handling the io channel')

    def process_io(self, msg):
        msg_type = msg['msg_type']
        # msg_id = msg['parent_header'].get('msg_id', 'dummy')
        # content = msg['content']
        if msg_type == 'status':
            pass
            # if content['execution_state'] == 'idle':
            #     self.log.debug('idle for: %s', msg_id)
            #     self.idle_future[msg_id].set_result(msg_id)
            #     self.idle_future[msg_id].set_result(msg_id)
        elif msg_type == 'clear_output':
            pass  # self.clear_output(cell.outputs, msg, cell_index)
        elif msg_type.startswith('comm'):
            self.handle_comm_msg(msg)
        # Check for remaining messages we don't process
        elif msg_type not in ['execute_input', 'update_display_data']:
            # Assign output as our processed "result"
            return self.output(msg)

    def output(self, msg):
        cell = self.cells[self.cell_index]
        output = nbformat.v4.output_from_msg(msg)
        if 'outputs' not in cell:
            cell.outputs = []
        self.log.debug("adding output to cell %r: %r", self.cell_index, output)
        cell.outputs.append(output)

    def handle_comm_msg(self, msg):
        pass

    @async_generator
    async def execute(self):
        for i, cell in enumerate(self.cells):
            cell = await self.execute_cell(i)
            await yield_(cell)

    @async_generator
    async def cell_generator(self, nb, kernel_id):
        async for cell in self.execute():
            await yield_(cell)

    async def execute_cell(self, index):
        self.cell_index = index
        cell = self.cells[self.cell_index]
        if cell.cell_type != 'code' or not cell.source.strip():
            return cell
        self.log.info('executing cell %r with source:\n%s', self.cell_index, cell.source)
        msg_id = await self.client.execute_async(cell.source)
        self.log.debug('execute msg_id: %r', msg_id)
        await self.idle_future[msg_id]
        self.log.info('execution of cell %r is done, with %r outputs: \n%r', self.cell_index, 'no' if not hasattr(cell, 'outputs') else len(cell.outputs), cell.outputs)
        return cell


async def main_execute(notebook):
    logging.basicConfig()
    # logging.getLogger()
    executor = CellExecutorAsyncio(notebook, os.getcwd())
    executor.log.setLevel('DEBUG')
    await executor.kernel_start()
    async for cell in executor.execute():
        if 'outputs' in cell:
            print(cell.outputs)
    nbformat.write(executor.notebook, 'output.ipynb')
    return


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='Execute a notebook')
    parser.add_argument('file', type=str, help='filename of notebook')
    args = parser.parse_args(args)
    print(args.file)
    nb = nbformat.read(args.file, as_version=4)
    import asyncio
    ioloop = asyncio.new_event_loop()
    asyncio.set_event_loop(ioloop)
    ioloop.run_until_complete(main_execute(nb))


if __name__ == '__main__':
    main()
