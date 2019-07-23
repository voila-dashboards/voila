#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os

import tornado.web

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.config_manager import recursive_update

from .execute import executenb
from .exporter import VoilaExporter


class VoilaHandler(JupyterHandler):

    def initialize(self, **kwargs):
        self.notebook_path = kwargs.pop('notebook_path', [])    # should it be []
        self.nbconvert_template_paths = kwargs.pop('nbconvert_template_paths', [])
        self.exporter_config = kwargs.pop('config', None)
        self.voila_configuration = kwargs['voila_configuration']

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def get(self, path=None):
        # if the handler got a notebook_path argument, always serve that
        notebook_path = self.notebook_path or path

        if self.voila_configuration.enable_nbextensions:
            # generate a list of nbextensions that are enabled for the classical notebook
            # a template can use that to load classical notebook extensions, but does not have to
            notebook_config = self.config_manager.get('notebook')
            # except for the widget extension itself, since voila has its own
            load_extensions = notebook_config.get('load_extensions', {})
            if 'jupyter-js-widgets/extension' in load_extensions:
                load_extensions['jupyter-js-widgets/extension'] = False
            if 'voila/extension' in load_extensions:
                load_extensions['voila/extension'] = False
            nbextensions = [name for name, enabled in load_extensions.items() if enabled]
        else:
            nbextensions = []

        model = self.contents_manager.get(path=notebook_path)
        if 'content' in model:
            notebook = model['content']
        else:
            raise tornado.web.HTTPError(404, 'file not found')

        # Fetch kernel name from the notebook metadata
        kernel_name = notebook.metadata.get('kernelspec', {}).get('name', self.kernel_manager.default_kernel_name)

        # Launch kernel and execute notebook
        cwd = os.path.dirname(notebook_path)
        kernel_id = yield tornado.gen.maybe_future(self.kernel_manager.start_kernel(kernel_name=kernel_name, path=cwd))
        km = self.kernel_manager.get_kernel(kernel_id)
        result = executenb(notebook, km=km, cwd=cwd)

        # render notebook to html
        resources = {
            'kernel_id': kernel_id,
            'base_url': self.base_url,
            'nbextensions': nbextensions,
            'theme': self.voila_configuration.theme
        }

        # add extra resources (necessary for reveal template)
        resources_reveal = {
            'reveal': {
                'theme': 'simple',
                'transition': 'slide',
                'scroll': False,
            }
        }
        resources.update(resources_reveal)

        # include potential extra resources
        extra_resources = self.voila_configuration.resources
        if extra_resources:
            recursive_update(resources, extra_resources)

        exporter = VoilaExporter(
            template_path=self.nbconvert_template_paths,
            config=self.exporter_config,
            contents_manager=self.contents_manager  # for the image inlining
        )

        if self.voila_configuration.strip_sources:
            exporter.exclude_input = True
            exporter.exclude_output_prompt = True
            exporter.exclude_input_prompt = True

        # Filtering out empty cells.
        def filter_empty_code_cells(cell):
            return (
                cell.cell_type != 'code' or                     # keep non-code cells
                (cell.outputs and not exporter.exclude_output)  # keep cell if output not excluded and not empty
                or not exporter.exclude_input                   # keep cell if input not excluded
            )
        result.cells = list(filter(filter_empty_code_cells, result.cells))

        html, resources = exporter.from_notebook_node(result, resources=resources)

        # Compose reply
        self.set_header('Content-Type', 'text/html')
        self.write(html)
