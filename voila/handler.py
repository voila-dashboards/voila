#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################


import os
from typing import Dict

import tornado.web
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.utils import url_path_join
from nbclient.util import ensure_async
from tornado.httputil import split_host_and_port
from traitlets.traitlets import Bool

from ._version import __version__
from .notebook_renderer import NotebookRenderer
from .query_parameters_handler import QueryStringSocketHandler
from .utils import ENV_VARIABLE


class VoilaHandler(JupyterHandler):
    def initialize(self, **kwargs):
        self.notebook_path = kwargs.pop('notebook_path', [])  # should it be []
        self.template_paths = kwargs.pop('template_paths', [])
        self.traitlet_config = kwargs.pop('config', None)
        self.voila_configuration = kwargs['voila_configuration']
        # we want to avoid starting multiple kernels due to template mistakes
        self.kernel_started = False

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

        # Adding request uri to kernel env
        kernel_env = os.environ.copy()
        kernel_env[ENV_VARIABLE.SCRIPT_NAME] = self.request.path
        kernel_env[
            ENV_VARIABLE.PATH_INFO
        ] = ''  # would be /foo/bar if voila.ipynb/foo/bar was supported
        kernel_env[ENV_VARIABLE.QUERY_STRING] = str(self.request.query)
        kernel_env[ENV_VARIABLE.SERVER_SOFTWARE] = 'voila/{}'.format(__version__)
        kernel_env[ENV_VARIABLE.SERVER_PROTOCOL] = str(self.request.version)
        host, port = split_host_and_port(self.request.host.lower())
        kernel_env[ENV_VARIABLE.SERVER_PORT] = str(port) if port else ''
        kernel_env[ENV_VARIABLE.SERVER_NAME] = host
        # Add HTTP Headers as env vars following rfc3875#section-4.1.18
        if len(self.voila_configuration.http_header_envs) > 0:
            for header_name in self.request.headers:
                config_headers_lower = [header.lower() for header in self.voila_configuration.http_header_envs]
                # Use case insensitive comparison of header names as per rfc2616#section-4.2
                if header_name.lower() in config_headers_lower:
                    env_name = f'HTTP_{header_name.upper().replace("-", "_")}'
                    kernel_env[env_name] = self.request.headers.get(header_name)

        template_arg = self.get_argument("voila-template", None)
        theme_arg = self.get_argument("voila-theme", None)

        # Compose reply
        self.set_header('Content-Type', 'text/html')
        self.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.set_header('Pragma', 'no-cache')
        self.set_header('Expires', '0')

        try:
            current_notebook_data: Dict = self.kernel_manager.notebook_data.get(notebook_path, {})
            pool_size: int = self.kernel_manager.get_pool_size(notebook_path)
        except AttributeError:
            # For server extenstion case.
            current_notebook_data = {}
            pool_size = 0
        # Check if the conditions for using pre-heated kernel are satisfied.
        if self.should_use_rendered_notebook(
            current_notebook_data,
            pool_size,
            template_arg,
            theme_arg,
            self.request.arguments,
        ):
            # Get the pre-rendered content of notebook, the result can be all rendered cells
            # of the notebook or some rendred cells and a generator which can be used by this
            # handler to continue rendering calls.

            render_task, rendered_cache, kernel_id = await self.kernel_manager.get_rendered_notebook(
                    notebook_name=notebook_path,
            )

            QueryStringSocketHandler.send_updates({'kernel_id': kernel_id, 'payload': self.request.query})
            # Send rendered cell to frontend
            if len(rendered_cache) > 0:
                self.write(''.join(rendered_cache))
                self.flush()

            # Wait for current running cell finish and send this cell to
            # frontend.
            rendered, rendering = await render_task
            if len(rendered) > len(rendered_cache):
                html_snippet = ''.join(rendered[len(rendered_cache):])
                self.write(html_snippet)
                self.flush()

            # Continue render cell from generator.
            async for html_snippet, _ in rendering:
                self.write(html_snippet)
                self.flush()
            self.flush()

        else:
            # All kernels are used or pre-heated kernel is disabled, start a normal kernel.
            gen = NotebookRenderer(
                voila_configuration=self.voila_configuration,
                traitlet_config=self.traitlet_config,
                notebook_path=notebook_path,
                template_paths=self.template_paths,
                config_manager=self.config_manager,
                contents_manager=self.contents_manager,
                base_url=self.base_url,
                kernel_spec_manager=self.kernel_spec_manager,
            )

            await gen.initialize(template=template_arg, theme=theme_arg)

            def time_out():
                """If not done within the timeout, we send a heartbeat
                this is fundamentally to avoid browser/proxy read-timeouts, but
                can be used in a template to give feedback to a user
                """

                self.write('<script>voila_heartbeat()</script>\n')
                self.flush()

            kernel_env[ENV_VARIABLE.VOILA_PREHEAT] = 'False'
            kernel_env[ENV_VARIABLE.VOILA_BASE_URL] = self.base_url
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
            async for html_snippet, _ in gen.generate_content_generator(
                kernel_id, kernel_future, time_out
            ):
                self.write(html_snippet)
                self.flush()
                # we may not want to consider not flusing after each snippet, but add an explicit flush function to the jinja context
                # yield  # give control back to tornado's IO loop, so it can handle static files or other requests
            self.flush()

    def redirect_to_file(self, path):
        self.redirect(url_path_join(self.base_url, 'voila', 'files', path))

    def should_use_rendered_notebook(
        self,
        notebook_data: Dict,
        pool_size: int,
        template_name: str,
        theme: str,
        request_args: Dict,
    ) -> Bool:
        if pool_size == 0:
            return False
        if len(notebook_data) == 0:
            return False

        rendered_template = notebook_data.get('template')
        rendered_theme = notebook_data.get('theme')
        if template_name is not None and template_name != rendered_template:
            return False
        if theme is not None and rendered_theme != theme:
            return False

        return True
