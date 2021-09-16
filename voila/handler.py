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
from typing import Dict, Union
from voila.voila_kernel_manager import VoilaKernelManager
from nbformat.notebooknode import NotebookNode

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
from .exporter import VoilaExporter
from .paths import collect_template_paths
from .notebook_renderer import NotebookRenderer


class VoilaHandler(JupyterHandler):
    def initialize(self, **kwargs):
        self.notebook_path = kwargs.pop("notebook_path", [])  # should it be []
        self.template_paths = kwargs.pop("template_paths", [])
        self.traitlet_config = kwargs.pop("config", None)
        self.voila_configuration = kwargs["voila_configuration"]
        self.notebook_renderer_factory = kwargs["notebook_renderer_factory"]
        # we want to avoid starting multiple kernels due to template mistakes
        self.kernel_started = False
        self.gen = NotebookRenderer(
            voila_configuration=self.voila_configuration,
            traitlet_config=self.traitlet_config,
            notebook_path=self.notebook_path,
            template_paths=self.template_paths,
            config_manager=self.config_manager,
            contents_manager=self.contents_manager,
            kernel_manager=self.kernel_manager,
            kernel_spec_manager=self.kernel_spec_manager,
        )

    @tornado.web.authenticated
    async def get(self, path=None):
        # if the handler got a notebook_path argument, always serve that
        notebook_path = self.notebook_path or path
        if (
            self.notebook_path and path
        ):  # when we are in single notebook mode but have a path
            self.redirect_to_file(path)
            return
        cwd = os.path.dirname(notebook_path)
        # if self.voila_configuration.enable_nbextensions:
        #     # generate a list of nbextensions that are enabled for the classical notebook
        #     # a template can use that to load classical notebook extensions, but does not have to
        #     notebook_config = self.config_manager.get('notebook')
        #     # except for the widget extension itself, since Voilà has its own
        #     load_extensions = notebook_config.get('load_extensions', {})
        #     if 'jupyter-js-widgets/extension' in load_extensions:
        #         load_extensions['jupyter-js-widgets/extension'] = False
        #     if 'voila/extension' in load_extensions:
        #         load_extensions['voila/extension'] = False
        #     nbextensions = [name for name, enabled in load_extensions.items() if enabled]
        # else:
        #     nbextensions = []

        # notebook = await self.load_notebook(notebook_path)
        # if not notebook:
        #     return

        # path, basename = os.path.split(notebook_path)
        # notebook_name = os.path.splitext(basename)[0]

        # Adding request uri to kernel env
        kernel_env = os.environ.copy()
        kernel_env["SCRIPT_NAME"] = self.request.path
        kernel_env[
            "PATH_INFO"
        ] = ""  # would be /foo/bar if voila.ipynb/foo/bar was supported
        kernel_env["QUERY_STRING"] = str(self.request.query)
        kernel_env["SERVER_SOFTWARE"] = "voila/{}".format(__version__)
        kernel_env["SERVER_PROTOCOL"] = str(self.request.version)
        host, port = split_host_and_port(self.request.host.lower())
        kernel_env["SERVER_PORT"] = str(port) if port else ""
        kernel_env["SERVER_NAME"] = host

        # Add HTTP Headers as env vars following rfc3875#section-4.1.18
        if len(self.voila_configuration.http_header_envs) > 0:
            config_headers_lower = [header.lower() for header in self.voila_configuration.http_header_envs]
            for header_name in self.request.headers:
                # Use case insensitive comparison of header names as per rfc2616#section-4.2
                if header_name.lower() in config_headers_lower:
                    env_name = f'HTTP_{header_name.upper().replace("-", "_")}'
                    self.kernel_env[env_name] = self.request.headers.get(header_name)

        # we can override the template via notebook metadata or a query parameter
        # template_override = None
        # if 'voila' in notebook.metadata and self.voila_configuration.allow_template_override in ['YES', 'NOTEBOOK']:
        #     template_override = notebook.metadata['voila'].get('template')
        # if self.voila_configuration.allow_template_override == 'YES':
        #     template_override = self.get_argument("voila-template", template_override)
        # if template_override:
        #     self.template_paths = collect_template_paths(['voila', 'nbconvert'], template_override)
        # template_name = template_override or self.voila_configuration.template

        # theme = self.voila_configuration.theme
        # if 'voila' in notebook.metadata and self.voila_configuration.allow_theme_override in ['YES', 'NOTEBOOK']:
        #     theme = notebook.metadata['voila'].get('theme', theme)
        # if self.voila_configuration.allow_theme_override == 'YES':
        #     theme = self.get_argument("voila-theme", theme)

        # # render notebook to html
        # resources = {
        #     'base_url': self.base_url,
        #     'nbextensions': nbextensions,
        #     'theme': theme,
        #     'template': template_name,
        #     'metadata': {
        #         'name': notebook_name
        #     }
        # }

        # # include potential extra resources
        # extra_resources = self.voila_configuration.config.VoilaConfiguration.resources
        # # if no resources get configured from neither the CLI nor a config file,
        # # extra_resources is a traitlets.config.loader.LazyConfigValue object
        # # This seems to only happy with the notebook server and traitlets 5
        # # Note that we use string checking for backward compatibility
        # if 'DeferredConfigString' in str(type(extra_resources)):
        #     from .configuration import VoilaConfiguration
        #     extra_resources = VoilaConfiguration.resources.from_string(extra_resources)
        # if not isinstance(extra_resources, dict):
        #     extra_resources = extra_resources.to_dict()
        # if extra_resources:
        #     recursive_update(resources, extra_resources)

        # Compose reply
        self.set_header("Content-Type", "text/html")
        self.set_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "0")
        # render notebook in snippets, and flush them out to the browser can render progresssively

        if isinstance(self.kernel_manager, VoilaKernelManager):
            notebook_html_dict: Dict = self.kernel_manager.notebook_html
            notebook_model: Union[
                NotebookNode, None
            ] = self.kernel_manager.notebook_model.get(notebook_path, None)
            # If we have a heated kernel in pool, use it
            print("in this case", len(notebook_html_dict))
            if len(notebook_html_dict) > 0:

                kernel_id: str = await ensure_async(
                    self.kernel_manager.start_kernel(
                        kernel_name=notebook_model.metadata.kernelspec.name,
                        path=cwd,
                        env=kernel_env,
                    )
                )
                notebook_html = notebook_html_dict.pop(kernel_id, None)
                if notebook_html is not None:
                    self.write(notebook_html)
                    self.flush()
            else:
                # All heated kernel used, instead of waitting,
                # start a normal kernel
                gen = self.notebook_renderer_factory()
                await gen.initialize()

                def time_out():
                    self.write("<script>voila_heartbeat()</script>\n")
                    self.flush()

                kernel_id = await ensure_async(
                    (
                        self.kernel_manager.start_kernel(
                            kernel_name=gen.notebook.metadata.kernelspec.name,
                            path=cwd,
                            env=kernel_env,
                            need_refill=False,
                        )
                    )
                )
                kernel_future = self.kernel_manager.get_kernel(kernel_id)
                async for html_snippet, resources in gen.generate_html(
                    kernel_id, kernel_future, time_out
                ):
                    self.write(html_snippet)
                    self.flush()
                    # we may not want to consider not flusing after each snippet, but add an explicit flush function to the jinja context
                    # yield  # give control back to tornado's IO loop, so it can handle static files or other requests
                self.flush()
        else:
            gen = self.notebook_renderer_factory()
            await gen.initialize()

            def time_out():
                self.write("<script>voila_heartbeat()</script>\n")
                self.flush()

            kernel_id = await ensure_async(
                (
                    self.kernel_manager.start_kernel(
                        kernel_name=gen.notebook.metadata.kernelspec.name,
                        path=cwd,
                        env=kernel_env,
                    )
                )
            )
            kernel_future = self.kernel_manager.get_kernel(kernel_id)

            async for html_snippet, resources in gen.generate_html(
                kernel_id, kernel_future, time_out
            ):
                self.write(html_snippet)
                self.flush()
                # we may not want to consider not flusing after each snippet, but add an explicit flush function to the jinja context
                # yield  # give control back to tornado's IO loop, so it can handle static files or other requests
            self.flush()

    def redirect_to_file(self, path):
        self.redirect(url_path_join(self.base_url, "voila", "files", path))
