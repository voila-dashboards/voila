#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import tornado.web

from jupyter_server.base.handlers import JupyterHandler

import nbformat
from nbconvert.preprocessors.execute import executenb
from nbconvert import HTMLExporter

from .paths import TEMPLATE_ROOT


class VoilaHandler(JupyterHandler):
    def initialize(self, notebook_path=None, strip_sources=True):
        self.notebook_path = notebook_path
        self.strip_sources = strip_sources

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def get(self, path=None):
        if path:
            path += '.ipynb'  # when used as a jupyter server extension, we don't use the extension
        # if the handler got a notebook_path argument, always serve that
        notebook_path = self.notebook_path or path

        model = self.contents_manager.get(path=notebook_path)
        if 'content' in model:
            notebook = model['content']
        else:
            raise tornado.web.HTTPError(404, 'file not found')

        # Ignore requested kernel name and make use of the one specified in the notebook.
        kernel_name = notebook.metadata.get('kernelspec', {}).get('name', self.kernel_manager.default_kernel_name)

        # Launch kernel and execute notebook.
        kernel_id = yield tornado.gen.maybe_future(self.kernel_manager.start_kernel(kernel_name=kernel_name))
        km = self.kernel_manager.get_kernel(kernel_id)
        result = executenb(notebook, km=km)

        # render notebook to html
        resources = {
            'kernel_id': kernel_id,
            'base_url': self.base_url
        }

        # I don't think this functionality is in nbconvert,
        # maybe we want to put this behind a flag
        def filter_empty_output(cell):
            return cell.cell_type != 'code' or len(cell.outputs) > 0
        result.cells = list(filter(filter_empty_output, result.cells))

        html, resources = HTMLExporter(
                template_file='voila.html',
                template_path=self.settings['template_paths'],
                exclude_input=self.strip_sources,
                exclude_output_prompt=self.strip_sources,
                exclude_input_prompt=self.strip_sources
            ).from_notebook_node(result, resources=resources)

        # Compose reply
        self.set_header('Content-Type', 'text/html')
        self.write(html)

