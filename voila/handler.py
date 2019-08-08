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
from jupyter_server.utils import url_path_join
import nbformat

from .execute import executenb
from .exporter import VoilaExporter


class VoilaHandler(JupyterHandler):

    def initialize(self, **kwargs):
        self.notebook_path = kwargs.pop('notebook_path', [])    # should it be []
        self.nbconvert_template_paths = kwargs.pop('nbconvert_template_paths', [])
        self.traitlet_config = kwargs.pop('config', None)
        self.voila_configuration = kwargs['voila_configuration']

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def get(self, path=None):
        # if the handler got a notebook_path argument, always serve that
        notebook_path = self.notebook_path or path
        if self.notebook_path and path:  # when we are in single notebook mode but have a path
            self.redirect_to_file(path)
            return

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

        notebook = yield self.load_notebook(notebook_path)
        if not notebook:
            return

        # Launch kernel and execute notebook
        cwd = os.path.dirname(notebook_path)

        # render notebook to html
        resources = {
            'base_url': self.base_url,
            'nbextensions': nbextensions,
            'theme': self.voila_configuration.theme
        }

        # include potential extra resources
        extra_resources = self.voila_configuration.resources
        if extra_resources:
            recursive_update(resources, extra_resources)

        exporter = VoilaExporter(
            template_path=self.nbconvert_template_paths,
            config=self.traitlet_config,
            contents_manager=self.contents_manager  # for the image inlining
        )
        if self.voila_configuration.strip_sources:
            exporter.exclude_input = True
            exporter.exclude_output_prompt = True
            exporter.exclude_input_prompt = True

        cwd = os.path.dirname(notebook_path)
        # we want to avoid starting multiple kernels due to template mistakes
        self.kernel_started = False

        # Filter for empty cells.
        def filter_empty_code_cells(cell):
            return (
                cell.cell_type != 'code' or                     # keep non-code cells
                (cell.outputs and not exporter.exclude_output)  # keep cell if output not excluded and not empty
                or not exporter.exclude_input                   # keep cell if input not excluded
            )

        @tornado.gen.coroutine
        def kernel_start():
            assert not self.kernel_started
            # Launch kernel
            kernel_id = yield tornado.gen.maybe_future(self.kernel_manager.start_kernel(kernel_name=notebook.metadata.kernelspec.name, path=cwd))
            self.kernel_started = True
            raise tornado.gen.Return(kernel_id)

        def notebook_execute(nb, kernel_id):
            km = self.kernel_manager.get_kernel(kernel_id)
            result = executenb(notebook, km=km, cwd=cwd, config=self.traitlet_config)
            result.cells = list(filter(filter_empty_code_cells, result.cells))
            # we modify the notebook in place, since the nb variable cannot be reassigned it seems in jinja2
            # e.g. if we do {% with nb = notebook_execute(nb, kernel_id) %}, the base template/blocks will not
            # see the updated variable (it seems to be local to our block)
            nb.cells = result.cells

        def cell_generator(nb, kernel_id):
            """Generator that will execute a single notebook cell at a time"""
            km = self.kernel_manager.get_kernel(kernel_id)

            all_cells = list(nb.cells)  # copy the cells, since we will modify in place
            for cell in all_cells:
                # we execute one cell at a time
                nb.cells = [cell]  # reuse the same notebook
                result = executenb(nb, km=km, cwd=cwd, config=self.traitlet_config)
                cell = result.cells[0]  # keep a reference to the executed cell
                nb.cells = all_cells  # restore notebook in case we access it from the template
                # we don't filter empty cells, since we do not know how many empty code cells we will have
                yield cell

        # these functions allow the start of a kernel and execution of the notebook after (parts of) the template
        # has been rendered and send to the client to allow progressive rendering.
        extra_context = {
            'kernel_start': lambda: kernel_start().result(),  # pass the result (not the future) to the template
            'cell_generator': cell_generator,
            'notebook_execute': notebook_execute,
        }

        # Compose reply
        self.set_header('Content-Type', 'text/html')
        # render notebook in snippets, and flush them out to the browser can render progresssively
        for html_snippet, resources in exporter.generate_from_notebook_node(notebook, resources=resources, extra_context=extra_context):
            self.write(html_snippet)
            self.flush()
        self.flush()

    def redirect_to_file(self, path):
        self.redirect(url_path_join(self.base_url, 'voila', 'files', path))

    @tornado.gen.coroutine
    def load_notebook(self, path):
        model = self.contents_manager.get(path=path)
        if 'content' not in model:
            raise tornado.web.HTTPError(404, 'file not found')
        if model.get('type') == 'notebook':
            notebook = model['content']
            notebook = yield self.fix_notebook(notebook)
            raise tornado.gen.Return(notebook)  # TODO py2: replace by return
        else:
            self.redirect_to_file(path)
            raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def fix_notebook(self, notebook):
        """Returns a notebook object with a valid kernelspec.

        In case the kernel is not found, we search for a matching kernel based on the language.
        """

        # Fetch kernel name from the notebook metadata
        if 'kernelspec' not in notebook.metadata:
            notebook.metadata.kernelspec = nbformat.NotebookNode()
        kernelspec = notebook.metadata.kernelspec
        kernel_name = kernelspec.get('name', self.kernel_manager.default_kernel_name)
        # We use `maybe_future` to support RemoteKernelSpecManager
        all_kernel_specs = yield tornado.gen.maybe_future(self.kernel_spec_manager.get_all_specs())
        # Find a spec matching the language if the kernel name does not exist in the kernelspecs
        if kernel_name not in all_kernel_specs:
            missing_kernel_name = kernel_name
            kernel_name = yield self.find_kernel_name_for_language(kernelspec.language.lower(), kernel_specs=all_kernel_specs)
            self.log.warning('Could not find a kernel named %r, will use  %r', missing_kernel_name, kernel_name)
        # We make sure the notebook's kernelspec is correct
        notebook.metadata.kernelspec.name = kernel_name
        notebook.metadata.kernelspec.display_name = all_kernel_specs[kernel_name]['spec']['display_name']
        notebook.metadata.kernelspec.language = all_kernel_specs[kernel_name]['spec']['language']
        raise tornado.gen.Return(notebook)  # TODO py2: replace by return

    @tornado.gen.coroutine
    def find_kernel_name_for_language(self, kernel_language, kernel_specs=None):
        """Finds a best matching kernel name given a kernel language.

        If multiple kernels matches are found, we try to return the same kernel name each time.
        """
        if kernel_specs is None:
            kernel_specs = yield tornado.gen.maybe_future(self.kernel_spec_manager.get_all_specs())
        matches = [
            name for name, kernel in kernel_specs.items()
            if kernel["spec"]["language"].lower() == kernel_language
        ]
        if matches:
            # Sort by display name to get the same kernel each time.
            matches.sort(key=lambda name: kernel_specs[name]["spec"]["display_name"])
            raise tornado.gen.Return(matches[0])  # TODO py2: replace by return
        else:
            raise tornado.web.HTTPError(500, 'No Jupyter kernel for language %r found' % kernel_language)
