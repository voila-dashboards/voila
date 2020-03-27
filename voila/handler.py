#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os

import tornado.web

import nbformat
from jupyter_server.utils import url_path_join
from jupyter_server.extension.handler import ExtensionHandlerMixin
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.config_manager import recursive_update
from nbconvert.preprocessors import ClearOutputPreprocessor

from .execute import executenb, VoilaExecutePreprocessor
from .exporter import VoilaExporter


class VoilaHandler(ExtensionHandlerMixin, JupyterHandler):

    def initialize(self, **kwargs):
        self.kernel_started = False
        super(VoilaHandler, self).initialize(**kwargs)

    @property
    def notebook_path(self):
        path = self.settings.get("notebook_path")
        # Get relative path to notebook.
        if path:  # path can be '', which is the default of ServerApp.file_to_run
            path = os.path.relpath(path, self.config["root_dir"])
        return path

    @tornado.web.authenticated
    async def get(self, path=None):
        # if the handler got a notebook_path argument, always serve that
        notebook_path = self.notebook_path or path
        if self.notebook_path and path:  # when we are in single notebook mode but have a path
            self.redirect_to_file(path)
            return

        if self.config.enable_nbextensions:
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

        self.notebook = await self.load_notebook(notebook_path)
        if not self.notebook:
            return
        self.cwd = os.path.dirname(notebook_path)

        path, basename = os.path.split(notebook_path)
        notebook_name = os.path.splitext(basename)[0]

        # render notebook to html
        resources = {
            'base_url': self.base_url,
            'nbextensions': nbextensions,
            'theme': self.config.theme,
            'metadata': {
                'name': notebook_name
            }
        }

        # include potential extra resources
        extra_resources = self.server_config.traitlet_configuration
        # if no resources get configured from neither the CLI nor a config file,
        # extra_resources is a traitlets.config.loader.LazyConfigValue object
        if not isinstance(extra_resources, dict):
            extra_resources = extra_resources.to_dict()
        extra_resources = extra_resources.get('resources')
        if extra_resources:
            recursive_update(resources, extra_resources)

        self.exporter = VoilaExporter(
            template_path=self.config.nbconvert_template_paths,
            config=self.server_config,
            contents_manager=self.contents_manager  # for the image inlining
        )
        if self.config.strip_sources:
            self.exporter.exclude_input = True
            self.exporter.exclude_output_prompt = True
            self.exporter.exclude_input_prompt = True

        # These functions allow the start of a kernel and execution of the notebook after (parts of) the template
        # has been rendered and send to the client to allow progressive rendering.
        # Template should first call kernel_start, and then decide to use notebook_execute
        # or cell_generator to implement progressive cell rendering
        extra_context = {
            # NOTE: we can remove the lambda is we use jinja's async feature, which will automatically await the future
            'kernel_start': lambda: self._jinja_kernel_start().result(),  # pass the result (not the future) to the template
            'cell_generator': self._jinja_cell_generator,
            'notebook_execute': self._jinja_notebook_execute,
        }

        # Currenly _jinja_kernel_start is executed from a different thread, which causes the websocket connection from
        # the frontend to fail. Instead, we start it beforehand, and just return the kernel_id in _jinja_kernel_start
        self.kernel_id = await self.kernel_manager.start_kernel(kernel_name=self.notebook.metadata.kernelspec.name, path=self.cwd)

        # Compose reply
        self.set_header('Content-Type', 'text/html')
        # render notebook in snippets, and flush them out to the browser can render progresssively
        async for html_snippet, resources in self.exporter.generate_from_notebook_node(self.notebook, resources=resources, extra_context=extra_context):
            self.write(html_snippet)
            self.flush()  # we may not want to consider not flusing after each snippet, but add an explicit flush function to the jinja context
            # yield  # give control back to tornado's IO loop, so it can handle static files or other requests
        self.flush()

    def redirect_to_file(self, path):
        self.redirect(url_path_join(self.base_url, 'voila', 'files', path))

    @tornado.gen.coroutine
    def _jinja_kernel_start(self):
        assert not self.kernel_started, "kernel was already started"
        # See command above aboout not being able to start the kernel from a different thread
        self.kernel_started = True
        return self.kernel_id

    def _jinja_notebook_execute(self, nb, kernel_id):
        km = self.kernel_manager.get_kernel(kernel_id)
        result = executenb(nb, km=km, cwd=self.cwd, config=self.server_config)
        # we modify the notebook in place, since the nb variable cannot be reassigned it seems in jinja2
        # e.g. if we do {% with nb = notebook_execute(nb, kernel_id) %}, the base template/blocks will not
        # see the updated variable (it seems to be local to our block)
        nb.cells = result.cells

    def _jinja_cell_generator(self, nb, kernel_id):
        """Generator that will execute a single notebook cell at a time"""
        km = self.kernel_manager.get_kernel(kernel_id)

        nb, resources = ClearOutputPreprocessor().preprocess(nb, {'metadata': {'path': self.cwd}})
        ep = VoilaExecutePreprocessor(config=self.server_config)

        stop_execution = False
        with ep.setup_preprocessor(nb, resources, km=km):
            for cell_idx, cell in enumerate(nb.cells):
                if stop_execution:
                    break
                try:
                    res = ep.preprocess_cell(cell, resources, cell_idx, store_history=False)
                except TimeoutError:
                    res = (cell, resources)
                    stop_execution = True

                yield res[0]

    # @tornado.gen.coroutine
    async def load_notebook(self, path):
        model = self.contents_manager.get(path=path)
        if 'content' not in model:
            raise tornado.web.HTTPError(404, 'file not found')
        __, extension = os.path.splitext(model.get('path', ''))
        if model.get('type') == 'notebook':
            notebook = model['content']
            notebook = await self.fix_notebook(notebook)
            return notebook
        elif extension in self.config.extension_language_mapping:
            language = self.config.extension_language_mapping[extension]
            notebook = await self.create_notebook(model, language=language)
            return notebook
        else:
            self.redirect_to_file(path)
            return None

    async def fix_notebook(self, notebook):
        """Returns a notebook object with a valid kernelspec.

        In case the kernel is not found, we search for a matching kernel based on the language.
        """

        # Fetch kernel name from the notebook metadata
        if 'kernelspec' not in notebook.metadata:
            notebook.metadata.kernelspec = nbformat.NotebookNode()
        kernelspec = notebook.metadata.kernelspec
        kernel_name = kernelspec.get('name', self.kernel_manager.default_kernel_name)
        # We use `maybe_future` to support RemoteKernelSpecManager
        all_kernel_specs = await tornado.gen.maybe_future(self.kernel_spec_manager.get_all_specs())
        # Find a spec matching the language if the kernel name does not exist in the kernelspecs
        if kernel_name not in all_kernel_specs:
            missing_kernel_name = kernel_name
            kernel_name = await self.find_kernel_name_for_language(kernelspec.language.lower(), kernel_specs=all_kernel_specs)
            self.log.warning('Could not find a kernel named %r, will use  %r', missing_kernel_name, kernel_name)
        # We make sure the notebook's kernelspec is correct
        notebook.metadata.kernelspec.name = kernel_name
        notebook.metadata.kernelspec.display_name = all_kernel_specs[kernel_name]['spec']['display_name']
        notebook.metadata.kernelspec.language = all_kernel_specs[kernel_name]['spec']['language']
        return notebook

    async def create_notebook(self, model, language):
        all_kernel_specs = await tornado.gen.maybe_future(self.kernel_spec_manager.get_all_specs())
        kernel_name = await self.find_kernel_name_for_language(language, kernel_specs=all_kernel_specs)
        spec = all_kernel_specs[kernel_name]
        notebook = nbformat.v4.new_notebook(
            metadata={
                'kernelspec': {
                    'display_name': spec['spec']['display_name'],
                    'language': spec['spec']['language'],
                    'name': kernel_name
                }
            },
            cells=[nbformat.v4.new_code_cell(model['content'])],
        )
        return notebook

    async def find_kernel_name_for_language(self, kernel_language, kernel_specs=None):
        """Finds a best matching kernel name given a kernel language.

        If multiple kernels matches are found, we try to return the same kernel name each time.
        """
        if kernel_language in self.config.language_kernel_mapping:
            return self.config.language_kernel_mapping[kernel_language]
        if kernel_specs is None:
            kernel_specs = await tornado.gen.maybe_future(self.kernel_spec_manager.get_all_specs())
        matches = [
            name for name, kernel in kernel_specs.items()
            if kernel["spec"]["language"].lower() == kernel_language.lower()
        ]
        if matches:
            # Sort by display name to get the same kernel each time.
            matches.sort(key=lambda name: kernel_specs[name]["spec"]["display_name"])
            return matches[0]
        else:
            raise tornado.web.HTTPError(500, 'No Jupyter kernel for language %r found' % kernel_language)
