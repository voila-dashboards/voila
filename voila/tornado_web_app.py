import os

import tornado.web

from jupyter_server.utils import url_path_join
from jupyter_server.services.kernels.handlers import KernelHandler, ZMQChannelsHandler
from jupyter_server.base.handlers import FileFindHandler, path_regex
from .shutdown_kernel_handler import VoilaShutdownKernelHandler
from .static_file_handler import MultiStaticFileHandler, TemplateStaticFileHandler, WhiteListFileHandler
from .query_parameters_handler import QueryStringSocketHandler
from .handler import VoilaHandler
from .treehandler import VoilaTreeHandler


_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"


def web_app(voila_app, env, preheat_kernel):
    voila_app.app = tornado.web.Application(
        base_url=voila_app.base_url,
        server_url=voila_app.server_url or voila_app.base_url,
        kernel_manager=voila_app.kernel_manager,
        kernel_spec_manager=voila_app.kernel_spec_manager,
        allow_remote_access=True,
        autoreload=voila_app.autoreload,
        voila_jinja2_env=env,
        jinja2_env=env,
        static_path='/',
        server_root_dir='/',
        contents_manager=voila_app.contents_manager,
        config_manager=voila_app.config_manager
    )

    voila_app.app.settings.update(voila_app.tornado_settings)

    handlers = []

    handlers.extend([
        (url_path_join(voila_app.server_url, r'/api/kernels/%s' % _kernel_id_regex), KernelHandler),
        (url_path_join(voila_app.server_url, r'/api/kernels/%s/channels' % _kernel_id_regex), ZMQChannelsHandler),
        (
            url_path_join(voila_app.server_url, r'/voila/templates/(.*)'),
            TemplateStaticFileHandler
        ),
        (
            url_path_join(voila_app.server_url, r'/voila/static/(.*)'),
            MultiStaticFileHandler,
            {
                'paths': voila_app.static_paths,
                'default_filename': 'index.html'
            },
        ),
        (url_path_join(voila_app.server_url, r'/voila/api/shutdown/(.*)'), VoilaShutdownKernelHandler)
    ])

    if preheat_kernel:
        handlers.append(
            (
                url_path_join(voila_app.server_url, r'/voila/query/%s' % _kernel_id_regex),
                QueryStringSocketHandler
            )
        )
    # Serving notebook extensions
    if voila_app.voila_configuration.enable_nbextensions:
        handlers.append(
            (
                url_path_join(voila_app.server_url, r'/voila/nbextensions/(.*)'),
                FileFindHandler,
                {
                    'path': voila_app.nbextensions_path,
                    'no_cache_paths': ['/'],  # don't cache anything in nbextensions
                },
            )
        )
    handlers.append(
        (
            url_path_join(voila_app.server_url, r'/voila/files/(.*)'),
            WhiteListFileHandler,
            {
                'whitelist': voila_app.voila_configuration.file_whitelist,
                'blacklist': voila_app.voila_configuration.file_blacklist,
                'path': voila_app.root_dir,
            },
        )
    )

    tree_handler_conf = {
        'voila_configuration': voila_app.voila_configuration
    }
    if voila_app.notebook_path:
        handlers.append((
            url_path_join(voila_app.server_url, r'/(.*)'),
            VoilaHandler,
            {
                'notebook_path': os.path.relpath(voila_app.notebook_path, voila_app.root_dir),
                'template_paths': voila_app.template_paths,
                'config': voila_app.config,
                'voila_configuration': voila_app.voila_configuration
            }
        ))
    else:
        voila_app.log.debug('serving directory: %r', voila_app.root_dir)
        handlers.extend([
            (voila_app.server_url, VoilaTreeHandler, tree_handler_conf),
            (url_path_join(voila_app.server_url, r'/voila/tree' + path_regex),
             VoilaTreeHandler, tree_handler_conf),
            (url_path_join(voila_app.server_url, r'/voila/render/(.*)'),
             VoilaHandler,
             {
                 'template_paths': voila_app.template_paths,
                 'config': voila_app.config,
                 'voila_configuration': voila_app.voila_configuration
            }),
        ])

    voila_app.app.add_handlers('.*$', handlers)
    voila_app.listen()
