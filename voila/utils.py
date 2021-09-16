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
from tornado.httputil import split_host_and_port
from .exporter import VoilaExporter
from .paths import collect_template_paths
import tornado.web

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.config_manager import recursive_update
from jupyter_server.utils import url_path_join
import nbformat

from nbconvert.preprocessors import ClearOutputPreprocessor
from nbclient.exceptions import CellExecutionError
from nbclient.util import ensure_async
from tornado.httputil import split_host_and_port

from ._version import __version__
from .execute import VoilaExecutor, strip_code_cell_warnings
from traitlets.config.configurable import LoggingConfigurable


def get_server_root_dir(settings):
    # notebook >= 5.0.0 has this in the settings
    if 'server_root_dir' in settings:
        return settings['server_root_dir']

    # This copies the logic added in the notebook in
    #  https://github.com/jupyter/notebook/pull/2234
    contents_manager = settings['contents_manager']
    root_dir = contents_manager.root_dir
    home = os.path.expanduser('~')
    if root_dir.startswith(home + os.path.sep):
        # collapse $HOME to ~
        root_dir = '~' + root_dir[len(home):]
    return root_dir

class GenerateNotebook(LoggingConfigurable):

    def __init__(self, **kwargs):
        self.notebook_path = kwargs.get('notebook_path', [])    # should it be []
        self.template_paths = kwargs.get('template_paths', [])
        self.traitlet_config = kwargs.get('config', None)
        self.voila_configuration = kwargs.get('voila_configuration')
        self.config_manager = kwargs.get('config_manager')
        self.contents_manager = kwargs.get('contents_manager')
        self.kernel_manager = kwargs.get('kernel_manager')
        self.kernel_spec_manager = kwargs.get('kernel_spec_manager')
        self.kernel_id = kwargs.get('kernel_id')
        self.base_url = '/'
        self.html = ''

    async def generate(self, path=None):
        # if the handler got a notebook_path argument, always serve that
        notebook_path = self.notebook_path or path

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

        # Adding request uri to kernel env
        self.kernel_env = os.environ.copy()
        predefined_env = {'SCRIPT_NAME': '/', 'PATH_INFO': '', 'QUERY_STRING': '', 'SERVER_SOFTWARE': 'voila/0.2.10', 'SERVER_PROTOCOL': 'HTTP/1.1', 'SERVER_PORT': '8866', 'SERVER_NAME': 'localhost'}
        self.kernel_env.update(predefined_env)

        # we can override the template via notebook metadata or a query parameter
        template_override = None
        if 'voila' in notebook.metadata and self.voila_configuration.allow_template_override in ['YES', 'NOTEBOOK']:
            template_override = notebook.metadata['voila'].get('template')
        if template_override:
            self.template_paths = collect_template_paths(['voila', 'nbconvert'], template_override)
        template_name = template_override or self.voila_configuration.template

        theme = self.voila_configuration.theme
        if 'voila' in notebook.metadata and self.voila_configuration.allow_theme_override in ['YES', 'NOTEBOOK']:
            theme = notebook.metadata['voila'].get('theme', theme)
        
        # render notebook to html
        resources = {
            'base_url': '/',
            'nbextensions': nbextensions,
            'theme': theme,
            'template': template_name,
            'metadata': {
                'name': notebook_name
            }
        }

        # include potential extra resources
        extra_resources = self.voila_configuration.config.VoilaConfiguration.resources
        # if no resources get configured from neither the CLI nor a config file,
        # extra_resources is a traitlets.config.loader.LazyConfigValue object
        # This seems to only happy with the notebook server and traitlets 5
        # Note that we use string checking for backward compatibility

        if 'DeferredConfigString' in str(type(extra_resources)):
            from .configuration import VoilaConfiguration
            extra_resources = VoilaConfiguration.resources.from_string(extra_resources)
        if not isinstance(extra_resources, dict):
            extra_resources = extra_resources.to_dict()
        if extra_resources:
            recursive_update(resources, extra_resources)

        self.exporter = VoilaExporter(
            template_paths=self.template_paths,
            template_name=template_name,
            config=self.traitlet_config,
            contents_manager=self.contents_manager,  # for the image inlining
            theme=theme,  # we now have the theme in two places
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

        # render notebook in snippets, and flush them out to the browser can render progresssively
        async for html_snippet, resources in self.exporter.generate_from_notebook_node(notebook, resources=resources, extra_context=extra_context):
            self.html += html_snippet      


    async def _jinja_kernel_start(self, nb):
        kernel_id = self.kernel_id
        print('kernel id', kernel_id)
        km = await ensure_async(self.kernel_manager.get_kernel(kernel_id))

        self.executor = VoilaExecutor(nb, km=km, config=self.traitlet_config,
                                      show_tracebacks=self.voila_configuration.show_tracebacks)

        ###
        # start kernel client
        self.executor.kc = km.client()
        await ensure_async(self.executor.kc.start_channels())
        await ensure_async(self.executor.kc.wait_for_ready(timeout=self.executor.startup_timeout))
        self.executor.kc.allow_stdin = False
        ###

        return kernel_id

    async def _jinja_notebook_execute(self, nb, kernel_id):
        print('\033[91m' + '_jinja_notebook_execute' + '\033[0m',)
        result = await self.executor.async_execute(cleanup_kc=False)
        # we modify the notebook in place, since the nb variable cannot be reassigned it seems in jinja2
        # e.g. if we do {% with nb = notebook_execute(nb, kernel_id) %}, the base template/blocks will not
        # see the updated variable (it seems to be local to our block)
        nb.cells = result.cells

    async def _jinja_cell_generator(self, nb, kernel_id):
        """Generator that will execute a single notebook cell at a time"""
        print('\033[91m' + '_jinja_cell_generator' + '\033[0m',)
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
            except CellExecutionError:
                self.log.exception('Error at server while executing cell: %r', input_cell)
                if self.executor.should_strip_error():
                    strip_code_cell_warnings(input_cell)
                    self.executor.strip_code_cell_errors(input_cell)
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
                            'ename': type(e).__name__,
                            'evalue': str(e),
                            'traceback': traceback.format_exception(*sys.exc_info()),
                        }
                    ]
            finally:
                yield output_cell

    async def load_notebook(self, path):
        model = await ensure_async(self.contents_manager.get(path=path))
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
        all_kernel_specs = await ensure_async(self.kernel_spec_manager.get_all_specs())
        # Find a spec matching the language if the kernel name does not exist in the kernelspecs
        if kernel_name not in all_kernel_specs:
            missing_kernel_name = kernel_name
            language = kernelspec.get('language', notebook.metadata.get('language_info', {}).get('name', ''))
            kernel_name = await self.find_kernel_name_for_language(language.lower(), kernel_specs=all_kernel_specs)
            self.log.warning('Could not find a kernel named %r, will use  %r', missing_kernel_name, kernel_name)
        # We make sure the notebook's kernelspec is correct
        notebook.metadata.kernelspec.name = kernel_name
        notebook.metadata.kernelspec.display_name = all_kernel_specs[kernel_name]['spec']['display_name']
        notebook.metadata.kernelspec.language = all_kernel_specs[kernel_name]['spec']['language']
        return notebook

    async def create_notebook(self, model, language):
        all_kernel_specs = await ensure_async(self.kernel_spec_manager.get_all_specs())
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
            kernel_specs = await ensure_async(self.kernel_spec_manager.get_all_specs())
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
 