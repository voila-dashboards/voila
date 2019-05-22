#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

from nbconvert.preprocessors.execute import ExecutePreprocessor
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
        self.outputs.append(output)
        self.sync_state()
        if hasattr(self.executor, 'widget_state'):
            # sync the state to the nbconvert state as well, since that is used for testing
            self.executor.widget_state[self.comm_id]['outputs'] = self.outputs

    def set_state(self, state):
        if 'msg_id' in state:
            msg_id = state.get('msg_id')
            if msg_id:
                self.executor.output_hook[msg_id] = self
                self.msg_id = msg_id
            else:
                del self.executor.output_hook[self.msg_id]
                self.msg_id = msg_id


class ExecutePreprocessorWithOutputWidget(ExecutePreprocessor):
    """Execute, but respect the output widget behaviour"""
    def preprocess(self, nb, resources, km=None):
        self.output_hook = {}
        self.output_objects = {}
        return super(ExecutePreprocessorWithOutputWidget, self).preprocess(nb, resources=resources, km=km)

    def output(self, outs, msg, display_id, cell_index):
        parent_msg_id = msg['parent_header'].get('msg_id')
        if parent_msg_id in self.output_hook:
            self.output_hook[parent_msg_id].output(outs, msg, display_id, cell_index)
            return
        super(ExecutePreprocessorWithOutputWidget, self).output(outs, msg, display_id, cell_index)

    def handle_comm_msg(self, outs, msg, cell_index):
        super(ExecutePreprocessorWithOutputWidget, self).handle_comm_msg(outs, msg, cell_index)
        self.log.debug('comm msg: %r', msg)
        if msg['msg_type'] == 'comm_open':
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
        if parent_msg_id in self.output_hook:
            self.output_hook[parent_msg_id].clear_output(outs, msg, cell_index)
            return
        super(ExecutePreprocessorWithOutputWidget, self).clear_output(outs, msg, cell_index)


def executenb(nb, cwd=None, km=None, **kwargs):
    resources = {}
    if cwd is not None:
        resources['metadata'] = {'path': cwd}  # pragma: no cover
    ep = ExecutePreprocessorWithOutputWidget(**kwargs)
    return ep.preprocess(nb, resources, km=km)[0]
