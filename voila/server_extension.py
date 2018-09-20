import os
import gettext
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import tornado.web

from jupyter_server.utils import url_path_join
from jupyter_server.base.handlers import path_regex

from .paths import ROOT, TEMPLATE_ROOT, STATIC_ROOT
from .handler import VoilaHandler
from .treehandler import VoilaTreeHandler
# from .watchdog import WatchDogHandler

def load_jupyter_server_extension(server_app):
    web_app = server_app.web_app

    jenv_opt = {"autoescape": True}
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_ROOT)), extensions=['jinja2.ext.i18n'], **jenv_opt)
    web_app.settings['voila_jinja2_env'] = env

    nbui = gettext.translation('nbui', localedir=str(ROOT / 'i18n'), fallback=True)
    env.install_gettext_translations(nbui, newstyle=False)

    host_pattern = '.*$'
    base_url = url_path_join(web_app.settings['base_url'])
    web_app.add_handlers(host_pattern, [
        (url_path_join(base_url, '/voila/render' + path_regex), VoilaHandler),
#         (url_path_join(base_url, '/voila/watchdog' + path_regex), WatchDogHandler),
        (url_path_join(base_url, '/voila'), VoilaTreeHandler),
        (url_path_join(base_url, '/voila/tree' + path_regex), VoilaTreeHandler),
        (url_path_join(base_url, '/voila/static/(.*)'),  tornado.web.StaticFileHandler, {'path': str(STATIC_ROOT)})
    ])
