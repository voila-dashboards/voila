#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################
import collections
import traitlets

from nbconvert.preprocessors import ClearOutputPreprocessor
from nbconvert.preprocessors.execute import CellExecutionError, ExecutePreprocessor
import tornado.gen
from ipykernel.jsonutil import json_clean


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
        content = msg['content']
        if 'data' not in content:
            output = {"output_type": "stream", "text": content['text'], "name": content['name']}
        else:
            data = content['data']
            output = {"output_type": "display_data", "data": data, "metadata": {}}
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
    def preprocess(self, nb, resources, km=None):
        self.output_hook_stack = collections.defaultdict(list)  # maps to list of hooks, where the last is used
        self.output_objects = {}
        try:
            result = super(VoilaExecutePreprocessor, self).preprocess(nb, resources=resources, km=km)
        except CellExecutionError as e:
            self.log.error(e)
            result = (nb, resources)
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


def executenb(nb, cwd=None, km=None, **kwargs):
    resources = {}
    if cwd is not None:
        resources['metadata'] = {'path': cwd}  # pragma: no cover
    # Clear any stale output, in case of exception
    nb, resources = ClearOutputPreprocessor().preprocess(nb, resources)
    ep = VoilaExecutePreprocessor(**kwargs)
    return ep.preprocess(nb, resources, km=km)[0]


class CellExecutor(traitlets.config.LoggingConfigurable):
    def __init__(self, notebook, cwd, multi_kernel_manager):
        self.notebook = notebook
        self.cwd = cwd
        self.multi_kernel_manager = multi_kernel_manager
        self.kernel_started = False

    @property
    def cells(self):
        return self.notebook.cells

    async def kernel_start(self):
        raise NotImplementedError

    async def cell_generator(self, nb, kernel_id):
        raise NotImplementedError

    def notebook_execute(self, nb, kernel_id):
        raise NotImplementedError


class CellExecutorNbConvert(CellExecutor):
    """Synchronous version of a cell executor, used for Python3.5"""
    def kernel_start(self):
        assert not self.kernel_started, "kernel was already started"

        @tornado.gen.coroutine
        def wrapper():
            # kernel_id = await tornado.gen.maybe_future(self.multi_kernel_manager.start_kernel(kernel_name=self.notebook.metadata.kernelspec.name, path=self.cwd))
            kernel_id = yield tornado.gen.maybe_future(self.multi_kernel_manager.start_kernel(kernel_name=self.notebook.metadata.kernelspec.name, path=self.cwd))
            return kernel_id
        kernel_id = wrapper().result()
        self.kernel_started = True
        return kernel_id

    def cell_generator(self, nb, kernel_id):
        """Generator that will execute a single notebook cell at a time"""
        assert self.kernel_started
        km = self.multi_kernel_manager.get_kernel(kernel_id)

        all_cells = list(nb.cells)  # copy the cells, since we will modify in place
        for cell in all_cells:
            # we execute one cell at a time
            nb.cells = [cell]  # reuse the same notebook
            result = executenb(nb, km=km, cwd=self.cwd)  # , config=self.traitlet_config)
            cell = result.cells[0]  # keep a reference to the executed cell
            nb.cells = all_cells  # restore notebook in case we access it from the template
            # we don't filter empty cells, since we do not know how many empty code cells we will have
            yield cell

    def notebook_execute(self, nb, kernel_id):
        assert self.kernel_started
        km = self.multi_kernel_manager.get_kernel(kernel_id)
        result = executenb(nb, km=km, cwd=self.cwd, parent=self.multi_kernel_manager)
        # result.cells = list(filter(lambda cell: filter_empty_code_cells(cell, self.exporter), result.cells))
        # we modify the notebook in place, since the nb variable cannot be reassigned it seems in jinja2
        # e.g. if we do {% with nb = notebook_execute(nb, kernel_id) %}, the base template/blocks will not
        # see the updated variable (it seems to be local to our block)
        nb.cells = result.cells
