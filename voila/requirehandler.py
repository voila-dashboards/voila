import requests
import logging
import tornado.web
import os

from jupyter_server.base.handlers import JupyterHandler
from jupyter_core.paths import (
    jupyter_data_dir, jupyter_config_path, jupyter_path,
    SYSTEM_JUPYTER_PATH, ENV_JUPYTER_PATH,
)

logger = logging.getLogger('Voila.require')

whitelist = ['jupyter-leaflet', 'ipyvolume', 'bqplot', 'threejs']


class RequireHandler(JupyterHandler):
    cdn = 'https://unpkg.com/{module}@{version}/dist/index.js'

    def initialize(self, cache_directories=None):
        self.cache_directories = cache_directories
        if self.cache_directories is None:
            self.cache_directories = [os.path.join(k, 'voila_cache') for k in [ENV_JUPYTER_PATH[0], jupyter_data_dir()]]
            logging.info('Using %r for caching directories', self.cache_directories)

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def get(self, path=None):
        if path:
            path = path.strip('/')  # remove leading /
        if '@' not in path:
            raise tornado.web.HTTPError(500)
        module, version = path.rsplit('@', 1)
        if module not in whitelist:
            logger.error('Module %r not in whitelist, will not cache', module)
            raise tornado.web.HTTPError(404)

        url = self.cdn.format(module=module, version=version)
        content = self.get_from_cache(module, version)
        if not content:
            logger.info('Request %s', url)
            response = requests.get(url)
            if response.ok:
                self.put_in_cache(module, version, response.text)
                content = response.text
            else:
                logger.error('Could not get: %r', path)
                raise tornado.web.HTTPError(500)

        self.set_header('Content-Type', 'text/javascript')
        self.write(content)

    def get_module_path(self, module, version):
        return '{module}/{version}'.format(module=module, version=version)

    def get_from_cache(self, module, version):
        path = self.get_module_path(module, version)
        for directory_path in self.cache_directories:
            cache_path = os.path.join(directory_path, path)
            try:
                logger.info('Try opening cache file: %s', cache_path)
                with open(cache_path) as f:
                    logger.info('Found cache file: %s', cache_path)
                    return f.read()
            except FileNotFoundError:
                pass

    def put_in_cache(self, module, version, value):
        path = self.get_module_path(module, version)
        for directory_path in self.cache_directories:
            cache_path = os.path.join(directory_path, path)
            directory_path = os.path.dirname(cache_path)
            if not os.path.exists(directory_path):
                try:
                    os.makedirs(directory_path)
                except:
                    pass
            try:
                logger.info('Try writing cache file: %s', cache_path)
                with open(cache_path, 'w') as f:
                    f.write(value)
                    logger.info('Wrote cache file: %s', cache_path)
                    return
            except FileNotFoundError:
                logger.info('Failed writing cache file: %s', cache_path)
