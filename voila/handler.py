#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import asyncio
import os
import sys
import traceback

import tornado.web

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.config_manager import recursive_update
from jupyter_server.utils import url_path_join
import nbformat

from nbconvert.preprocessors import ClearOutputPreprocessor
from nbclient.util import ensure_async

from .execute import VoilaExecutor
from .exporter import VoilaExporter


class VoilaHandler(JupyterHandler):

    def initialize(self, **kwargs):
        self.notebook_path = kwargs.pop('notebook_path', [])    # should it be []
        self.template_paths = kwargs.pop('template_paths', [])
        self.traitlet_config = kwargs.pop('config', None)
        self.voila_configuration = kwargs['voila_configuration']
        # we want to avoid starting multiple kernels due to template mistakes
        self.kernel_started = False

    @tornado.web.authenticated
    async def get(self, path=None):
        # if the handler got a notebook_path argument, always serve that
        notebook_path = self.notebook_path or path
        if self.notebook_path and path:  # when we are in single notebook mode but have a path
            self.redirect_to_file(path)
            return

        if self.voila_configuration.enable_nbextensions:
            # generate a list of nbextensions that are enabled for the classical notebook
            # a template can use that to load classical notebook extensions, but does not have to
            notebook_config = self.config_manager.get('notebook')
            # except for the widget extension itself, since Voilà has its own
            load_extensions = notebook_config.get('load_extensions', {})
            if 'jupyter-js-widgets/extension' in load_extensions:
                load_extensions['jupyter-js-widgets/extension'] = False
            if 'voila/extension' in load_extensions:
                load_extensions['voila/extension'] = False
            nbextensions = [name for name, enabled in load_extensions.items() if enabled]
        else:
            nbextensions = []

        notebook = await self.load_notebook(notebook_path)
        if not notebook:
            return
        self.cwd = os.path.dirname(notebook_path)

        path, basename = os.path.split(notebook_path)
        notebook_name = os.path.splitext(basename)[0]

        # render notebook to html
        resources = {
            'base_url': self.base_url,
            'nbextensions': nbextensions,
            'theme': self.voila_configuration.theme,
            'metadata': {
                'name': notebook_name
            }
        }

        # include potential extra resources
        extra_resources = self.voila_configuration.config.VoilaConfiguration.resources
        # if no resources get configured from neither the CLI nor a config file,
        # extra_resources is a traitlets.config.loader.LazyConfigValue object
        if not isinstance(extra_resources, dict):
            extra_resources = extra_resources.to_dict()
        if extra_resources:
            recursive_update(resources, extra_resources)

        self.exporter = VoilaExporter(
            template_paths=self.template_paths,
            config=self.traitlet_config,
            contents_manager=self.contents_manager,  # for the image inlining
            theme=self.voila_configuration.theme,  # we now have the theme in two places
            base_url=self.base_url,
        )
        if self.voila_configuration.strip_sources:
            self.exporter.exclude_input = True
            self.exporter.exclude_output_prompt = True
            self.exporter.exclude_input_prompt = True

        # These functions allow the start of a kernel and execution of the notebook after (parts of) the template
        # has been rendered and send to the client to allow progressive rendering.
        # Template should first call kernel_start, and then decide to use notebook_execute
        # or cell_generator to implement progressive cell rendering
        extra_context = {
            'kernel_start': self._jinja_kernel_start,
            'cell_generator': self._jinja_cell_generator,
            'notebook_execute': self._jinja_notebook_execute,
        }

        # Compose reply
        self.set_header('Content-Type', 'text/html')
        # render notebook in snippets, and flush them out to the browser can render progresssively
        async for html_snippet, resources in self.exporter.generate_from_notebook_node(notebook, resources=resources, extra_context=extra_context):
            self.write(html_snippet)
            self.flush()  # we may not want to consider not flusing after each snippet, but add an explicit flush function to the jinja context
            # yield  # give control back to tornado's IO loop, so it can handle static files or other requests
        self.flush()

    def redirect_to_file(self, path):
        self.redirect(url_path_join(self.base_url, 'voila', 'files', path))

    async def _jinja_kernel_start(self, nb):
        assert not self.kernel_started, "kernel was already started"

        kernel_id = await ensure_async(self.kernel_manager.start_kernel(
           kernel_name=nb.metadata.kernelspec.name,
           path=self.cwd
        ))
        km = self.kernel_manager.get_kernel(kernel_id)

        self.executor = VoilaExecutor(nb, km=km, config=self.traitlet_config)

        ###
        # start kernel client
        self.executor.kc = km.client()
        await ensure_async(self.executor.kc.start_channels())
        await ensure_async(self.executor.kc.wait_for_ready(timeout=self.executor.startup_timeout))
        self.executor.kc.allow_stdin = False
        ###

        self.kernel_started = True
        return kernel_id

    async def _jinja_notebook_execute(self, nb, kernel_id):
        result = await self.executor.async_execute(cleanup_kc=False)
        # we modify the notebook in place, since the nb variable cannot be reassigned it seems in jinja2
        # e.g. if we do {% with nb = notebook_execute(nb, kernel_id) %}, the base template/blocks will not
        # see the updated variable (it seems to be local to our block)
        nb.cells = result.cells

    async def _jinja_cell_generator(self, nb, kernel_id):
        """Generator that will execute a single notebook cell at a time"""
        nb, resources = ClearOutputPreprocessor().preprocess(nb, {'metadata': {'path': self.cwd}})
        for cell_idx, input_cell in enumerate(nb.cells):
            try:
                task = asyncio.ensure_future(self.executor.execute_cell(input_cell, None, cell_idx, store_history=False))
                while True:
                    done, pending = await asyncio.wait({task}, timeout=self.voila_configuration.http_keep_alive_timeout)
                    if pending:
                        # If not done within the timeout, we send a heartbeat
                        # this is fundamentally to avoid browser/proxy read-timeouts, but
                        # can be used in a template to give feedback to a user
                        self.write("<script>voila_heartbeat()</script>\n")
                        self.flush()
                        continue
                    output_cell = await task
                    break
            except TimeoutError:
                output_cell = input_cell
                break
            except Exception as e:
                self.log.exception('Error at server while executing cell: %r', input_cell)
                output_cell = nbformat.v4.new_code_cell()
                if self.executor.should_strip_error():
                    output_cell.outputs = [
                        {
                            "output_type": "stream",
                            "name": "stderr",
                            "text": "An exception occurred at the server (not the notebook). {}".format(self.executor.cell_error_instruction),
                        }
                    ]
                else:
                    output_cell.outputs = [
                        {
                            'output_type': 'error',
                            'ename': type(e).__name__,
                            'evalue': str(e),
                            'traceback': traceback.format_exception(*sys.exc_info()),
                        }
                    ]
            finally:
                yield output_cell

    async def load_notebook(self, path):
        model = self.contents_manager.get(path=path)
        if 'content' not in model:
            raise tornado.web.HTTPError(404, 'file not found')
        __, extension = os.path.splitext(model.get('path', ''))
        if model.get('type') == 'notebook':
            notebook = model['content']
            notebook = await self.fix_notebook(notebook)
            return notebook
        elif extension in self.voila_configuration.extension_language_mapping:
            language = self.voila_configuration.extension_language_mapping[extension]
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
        if kernel_language in self.voila_configuration.language_kernel_mapping:
            return self.voila_configuration.language_kernel_mapping[kernel_language]
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
