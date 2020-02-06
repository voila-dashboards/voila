#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################
import collections
import logging
try:
    from time import monotonic  # Py 3
except ImportError:
    from time import time as monotonic  # Py 2

from nbconvert.preprocessors import ClearOutputPreprocessor
from nbconvert.preprocessors.execute import CellExecutionError, ExecutePreprocessor
from nbformat.v4 import output_from_msg
import zmq

from traitlets import Unicode
from ipykernel.jsonutil import json_clean

try:
    TimeoutError  # Py 3
except NameError:
    TimeoutError = RuntimeError  # Py 2


def strip_code_cell_warnings(cell):
    """Strip any warning outputs and traceback from a code cell."""
    # There is no 'outputs' key for markdown cells
    if 'outputs' not in cell:
        return cell

    outputs = cell['outputs']

    cell['outputs'] = [
        output for output in outputs
        if output['output_type'] != 'stream' or output['name'] != 'stderr'
    ]

    return cell


def should_strip_error(config):
    """Return True if errors should be stripped from the Notebook, False otherwise, depending on the current config."""
    return 'Voila' not in config or 'log_level' not in config['Voila'] or config['Voila']['log_level'] != logging.DEBUG


class OutputWidget:
    """This class mimics a front end output widget"""
    def __init__(self, comm_id, state, kernel_client, executor):
        self.comm_id = comm_id
        self.state = state
        self.kernel_client = kernel_client
        self.executor = executor
        self.topic = ('comm-%s' % self.comm_id).encode('ascii')
        self.outputs = self.state['outputs']
        self.clear_before_next_output = False

    def clear_output(self, outs, msg, cell_index):
        self.parent_header = msg['parent_header']
        content = msg['content']
        if content.get('wait'):
            self.clear_before_next_output = True
        else:
            self.outputs = []
            # sync back the state to the kernel
            self.sync_state()
            if hasattr(self.executor, 'widget_state'):
                # sync the state to the nbconvert state as well, since that is used for testing
                self.executor.widget_state[self.comm_id]['outputs'] = self.outputs

    def sync_state(self):
        state = {'outputs': self.outputs}
        msg = {'method': 'update', 'state': state, 'buffer_paths': []}
        self.send(msg)

    def _publish_msg(self, msg_type, data=None, metadata=None, buffers=None, **keys):
        """Helper for sending a comm message on IOPub"""
        data = {} if data is None else data
        metadata = {} if metadata is None else metadata
        content = json_clean(dict(data=data, comm_id=self.comm_id, **keys))
        msg = self.kernel_client.session.msg(msg_type, content=content, parent=self.parent_header, metadata=metadata)
        self.kernel_client.shell_channel.send(msg)

    def send(self, data=None, metadata=None, buffers=None):
        self._publish_msg('comm_msg', data=data, metadata=metadata, buffers=buffers)

    def output(self, outs, msg, display_id, cell_index):
        if self.clear_before_next_output:
            self.outputs = []
            self.clear_before_next_output = False
        self.parent_header = msg['parent_header']
        output = output_from_msg(msg)

        if self.outputs:
            # try to coalesce/merge output text
            last_output = self.outputs[-1]
            if (last_output['output_type'] == 'stream' and
                    output['output_type'] == 'stream' and
                    last_output['name'] == output['name']):
                last_output['text'] += output['text']
            else:
                self.outputs.append(output)
        else:
            self.outputs.append(output)
        self.sync_state()
        if hasattr(self.executor, 'widget_state'):
            # sync the state to the nbconvert state as well, since that is used for testing
            self.executor.widget_state[self.comm_id]['outputs'] = self.outputs

    def set_state(self, state):
        if 'msg_id' in state:
            msg_id = state.get('msg_id')
            if msg_id:
                self.executor.register_output_hook(msg_id, self)
                self.msg_id = msg_id
            else:
                self.executor.remove_output_hook(self.msg_id, self)
                self.msg_id = msg_id


class VoilaExecutePreprocessor(ExecutePreprocessor):
    """Execute, but respect the output widget behaviour"""
    cell_error_instruction = Unicode(
        'Please run Voila with --debug to see the error message.',
        config=True,
        help=(
            'instruction given to user to debug cell errors'
        )
    )

    def __init__(self, **kwargs):
        super(VoilaExecutePreprocessor, self).__init__(**kwargs)
        self.output_hook_stack = collections.defaultdict(list)  # maps to list of hooks, where the last is used
        self.output_objects = {}

    def preprocess(self, nb, resources, km=None):
        try:
            result = super(VoilaExecutePreprocessor, self).preprocess(nb, resources=resources, km=km)
        except CellExecutionError as e:
            self.log.error(e)
            result = (nb, resources)

        # Strip errors and traceback if not in debug mode
        if should_strip_error(self.config):
            self.strip_notebook_errors(nb)

        return result

    def preprocess_cell(self, cell, resources, cell_index, store_history=True):
        try:
            # TODO: pass store_history as a 5th argument when we can require nbconver >=5.6.1
            # result = super(VoilaExecutePreprocessor, self).preprocess_cell(cell, resources, cell_index, store_history)
            result = super(VoilaExecutePreprocessor, self).preprocess_cell(cell, resources, cell_index)
        except CellExecutionError as e:
            self.log.error(e)
            result = (cell, resources)

        # Strip errors and traceback if not in debug mode
        if should_strip_error(self.config):
            strip_code_cell_warnings(cell)
            self.strip_code_cell_errors(cell)

        return result

    def register_output_hook(self, msg_id, hook):
        # mimics
        # https://jupyterlab.github.io/jupyterlab/services/interfaces/kernel.ikernelconnection.html#registermessagehook
        self.output_hook_stack[msg_id].append(hook)

    def remove_output_hook(self, msg_id, hook):
        # mimics
        # https://jupyterlab.github.io/jupyterlab/services/interfaces/kernel.ikernelconnection.html#removemessagehook
        removed_hook = self.output_hook_stack[msg_id].pop()
        assert removed_hook == hook

    def output(self, outs, msg, display_id, cell_index):
        parent_msg_id = msg['parent_header'].get('msg_id')
        if self.output_hook_stack[parent_msg_id]:
            hook = self.output_hook_stack[parent_msg_id][-1]
            hook.output(outs, msg, display_id, cell_index)
            return
        super(VoilaExecutePreprocessor, self).output(outs, msg, display_id, cell_index)

    def handle_comm_msg(self, outs, msg, cell_index):
        super(VoilaExecutePreprocessor, self).handle_comm_msg(outs, msg, cell_index)
        self.log.debug('comm msg: %r', msg)
        if msg['msg_type'] == 'comm_open' and msg['content'].get('target_name') == 'jupyter.widget':
            content = msg['content']
            data = content['data']
            state = data['state']
            comm_id = msg['content']['comm_id']
            if state['_model_module'] == '@jupyter-widgets/output' and state['_model_name'] == 'OutputModel':
                self.output_objects[comm_id] = OutputWidget(comm_id, state, self.kc, self)
        elif msg['msg_type'] == 'comm_msg':
            content = msg['content']
            data = content['data']
            if 'state' in data:
                state = data['state']
                comm_id = msg['content']['comm_id']
                if comm_id in self.output_objects:
                    self.output_objects[comm_id].set_state(state)

    def clear_output(self, outs, msg, cell_index):
        parent_msg_id = msg['parent_header'].get('msg_id')
        if self.output_hook_stack[parent_msg_id]:
            hook = self.output_hook_stack[parent_msg_id][-1]
            hook.clear_output(outs, msg, cell_index)
            return
        super(VoilaExecutePreprocessor, self).clear_output(outs, msg, cell_index)

    def strip_notebook_errors(self, nb):
        """Strip error messages and traceback from a Notebook."""
        cells = nb['cells']

        code_cells = [cell for cell in cells if cell['cell_type'] == 'code']

        for cell in code_cells:
            strip_code_cell_warnings(cell)
            self.strip_code_cell_errors(cell)

        return nb

    def strip_code_cell_errors(self, cell):
        """Strip any error outputs and traceback from a code cell."""
        # There is no 'outputs' key for markdown cells
        if 'outputs' not in cell:
            return cell

        outputs = cell['outputs']

        error_outputs = [output for output in outputs if output['output_type'] == 'error']

        error_message = 'There was an error when executing cell [{}]. {}'.format(cell['execution_count'], self.cell_error_instruction)

        for output in error_outputs:
            output['ename'] = 'ExecutionError'
            output['evalue'] = 'Execution error'
            output['traceback'] = [error_message]

        return cell

    # make it nbconvert 5.5 compatible
    def _get_timeout(self, cell):
        if self.timeout_func is not None and cell is not None:
            timeout = self.timeout_func(cell)
        else:
            timeout = self.timeout

        if not timeout or timeout < 0:
            timeout = None

        return timeout

    # make it nbconvert 5.5 compatible
    def _handle_timeout(self, timeout):
        self.log.error(
            "Timeout waiting for execute reply (%is)." % timeout)
        if self.interrupt_on_timeout:
            self.log.error("Interrupting kernel")
            self.km.interrupt_kernel()
        else:
            raise TimeoutError("Cell execution timed out")

    def run_cell(self, cell, cell_index=0, store_history=False):
        parent_msg_id = self.kc.execute(cell.source, store_history=store_history, stop_on_error=not self.allow_errors)
        self.log.debug("Executing cell:\n%s", cell.source)
        exec_timeout = self._get_timeout(cell)
        deadline = None
        if exec_timeout is not None:
            deadline = monotonic() + exec_timeout

        cell.outputs = []
        self.clear_before_next_output = False

        # we need to have a reply, and return to idle before we can consider the cell executed
        idle = False
        execute_reply = None
        while not idle or execute_reply is None:
            # we want to timeout regularly, to see if the kernel is still alive
            # this is tested in preprocessors/test/test_execute.py#test_kernel_death
            # this actually fakes the kernel death, and we might be able to use the xlist
            # to detect a disconnected kernel
            timeout = min(1, deadline - monotonic())
            # if we interrupt on timeout, we allow 1 seconds to pass till deadline
            # to make sure we get the interrupt message
            if timeout >= (-1 if self.interrupt_on_timeout else 0):
                # we include 0, which simply is a poll to see if we have messages left
                rlist = zmq.select([self.kc.iopub_channel.socket, self.kc.shell_channel.socket], [], [], timeout)[0]
                if not rlist:
                    self._check_alive()
                    if monotonic() > deadline:
                        self._handle_timeout(exec_timeout)
                if self.kc.shell_channel.socket in rlist:
                    msg = self.kc.shell_channel.get_msg(block=False)
                    if msg['parent_header'].get('msg_id') == parent_msg_id:
                        execute_reply = msg
                if self.kc.iopub_channel.socket in rlist:
                    msg = self.kc.iopub_channel.get_msg(block=False)
                    if msg['parent_header'].get('msg_id') == parent_msg_id:
                        if msg['msg_type'] == 'status' and msg['content']['execution_state'] == 'idle':
                            idle = True
                        else:
                            self.process_message(msg, cell, cell_index)
                    else:
                        self.log.debug("Received message for which we were not the parent: %s", msg)
            else:
                self._handle_timeout(exec_timeout)
                break

        return execute_reply, cell.outputs


def executenb(nb, cwd=None, km=None, **kwargs):
    resources = {}
    if cwd is not None:
        resources['metadata'] = {'path': cwd}  # pragma: no cover
    # Clear any stale output, in case of exception
    nb, resources = ClearOutputPreprocessor().preprocess(nb, resources)
    ep = VoilaExecutePreprocessor(**kwargs)
    return ep.preprocess(nb, resources, km=km)[0]
