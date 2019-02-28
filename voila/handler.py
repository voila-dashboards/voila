#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import tornado.web

from jupyter_server.base.handlers import JupyterHandler

import nbformat  # noqa: F401
from .execute import executenb
from nbconvert import HTMLExporter
import jinja2


class VoilaHandler(JupyterHandler):

    def initialize(self, **kwargs):
        self.notebook_path = kwargs.pop('notebook_path', [])    # should it be []
        self.strip_sources = kwargs.pop('strip_sources', True)
        self.nbconvert_template_paths = kwargs.pop('nbconvert_template_paths', [])
        self.exporter_config = kwargs.pop('config', None)

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def get(self, path=None):
        if path:
            path += '.ipynb'  # when used as a jupyter server extension, we don't use the extension
        # if the handler got a notebook_path argument, always serve that
        notebook_path = self.notebook_path or path

        # generate a list of nbextensions that are enabled for the classical notebook
        # a template can use that to load classical notebook extensions, but does not have to
        notebook_config = self.config_manager.get('notebook')
        # except for the widget extension itself, since voila has its own
        load_extensions = notebook_config.get('load_extensions', {})
        if "jupyter-js-widgets/extension" in load_extensions:
            load_extensions["jupyter-js-widgets/extension"] = False
        nbextensions = [name for name, enabled in load_extensions.items() if enabled]

        model = self.contents_manager.get(path=notebook_path)
        if 'content' in model:
            notebook = model['content']
        else:
            raise tornado.web.HTTPError(404, 'file not found')

        # before rendering/server the voila.tpl (nbconvert) template, we (optionally) send
        # an html page (voila.html template) to allow progressive loading.
        # A template can show a spinner for example, or already show a portion of the UI (SPA).

        resources = {}  # we may want to have resources similar to nbconvert for consistency
        resources['metadata'] = {'name': notebook_path}
        template = None
        try:
            template = self.get_template('voila.html')
        except jinja2.TemplateNotFound:
            pass  # voila.html is optional
        else:
            html = self.render_template(template,
                                        page_title='test',
                                        server_root=self.settings['server_root_dir'],
                                        nbextensions=nbextensions,
                                        path=path or '',
                                        nb=notebook,
                                        resources=resources
                                        )
            self.set_header('Content-Type', 'text/html')
            self.write(html)
            self.flush()  # next phase, flush html to client so it can render (progressive)

        # Fetch kernel name from the notebook metadata
        kernel_name = notebook.metadata.get('kernelspec', {}).get('name', self.kernel_manager.default_kernel_name)

        # Launch kernel and execute notebook
        kernel_id = yield tornado.gen.maybe_future(self.kernel_manager.start_kernel(kernel_name=kernel_name))
        km = self.kernel_manager.get_kernel(kernel_id)
        result = executenb(notebook, km=km)

        # render notebook to html
        resources = {
            'kernel_id': kernel_id,
            'base_url': self.base_url,
            'nbextensions': nbextensions
        }

        exporter = HTMLExporter(
            template_file='voila.tpl',
            template_path=self.nbconvert_template_paths,
            config=self.exporter_config
        )

        if self.strip_sources:
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
        self.write(html)
