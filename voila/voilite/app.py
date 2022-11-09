import logging
import os
import shutil
from distutils.dir_util import copy_tree
from typing import Dict

import nbformat
from jupyter_core.paths import jupyter_path
from jupyter_server.utils import url_path_join
from traitlets import List, Unicode, default
from traitlets.config.application import Application

from ..configuration import VoilaConfiguration
from ..utils import find_all_lab_theme, get_page_config
from .exporter import VoiliteExporter


def _(x):
    return x


class Voilite(Application):
    name = 'voilite'

    description = Unicode(
        """voila [OPTIONS] NOTEBOOK_FILENAME

        This launches a stand-alone server for read-only notebooks.
        """
    )
    option_description = Unicode(
        """
        notebook_path:
            File name of the Jupyter notebook to display.
        """
    )
    base_url = Unicode('/', config=True, help=_('Base URL'))
    notebook_filename = Unicode()
    root_dir = Unicode(
        config=True, help=_('The directory to use for notebooks.')
    )

    notebook_path = Unicode(
        None,
        config=True,
        allow_none=True,
        help=_('path to notebook to serve with Voilite'),
    )

    template_paths = List([], config=True, help=_('path to jinja2 templates'))

    classes = [VoilaConfiguration]

    aliases = {
        'strip_sources': 'VoilaConfiguration.strip_sources',
        'template': 'VoilaConfiguration.template',
        'theme': 'VoilaConfiguration.theme',
        'base_url': 'Voilite.base_url',
    }

    output_prefix = Unicode(
        '_output',
        config=True,
        help=_('Path to the output directory'),
    )

    @default('log_level')
    def _default_log_level(self):
        return logging.INFO

    @default('root_dir')
    def _default_root_dir(self):
        if self.notebook_path:
            return os.path.dirname(os.path.abspath(self.notebook_path))
        else:
            return os.getcwd()

    def initialize(self, argv=None):
        super().initialize(argv)
        if len(self.extra_args) == 1:
            arg = self.extra_args[0]

            if not self.notebook_path:
                if os.path.isdir(arg):
                    self.root_dir = arg
                elif os.path.isfile(arg):
                    self.notebook_path = arg
                else:
                    raise ValueError(
                        'argument is neither a file nor a directory: %r' % arg
                    )
        elif len(self.extra_args) != 0:
            raise ValueError(
                'provided more than 1 argument: %r' % self.extra_args
            )
        self.voilite_configuration = VoilaConfiguration(parent=self)

    def copy_static_files(self, page_config: Dict) -> None:

        lite_static_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'static'
        )
        dest_static_path = os.path.join(os.getcwd(), self.output_prefix)
        if os.path.isdir(dest_static_path):
            shutil.rmtree(dest_static_path, ignore_errors=False)
        copy_tree(
            os.path.join(lite_static_path),
            os.path.join(dest_static_path, 'build'),
        )
        shutil.copyfile(
            os.path.join(lite_static_path, 'services.js'),
            os.path.join(dest_static_path, 'services.js'),
        )

        # Copy extension files
        labextensions_path = jupyter_path('labextensions')
        federated_extensions = page_config.get('federated_extensions', [])
        roots = tuple(
            os.path.abspath(os.path.expanduser(p)) + os.sep
            for p in labextensions_path
        )
        dest_extension_path = os.path.join(dest_static_path, 'labextensions')
        if os.path.isdir(dest_extension_path):
            shutil.rmtree(dest_extension_path)
        for extension in federated_extensions:
            for root in roots:
                name = extension['name']
                full_path = os.path.join(root, name)
                if os.path.isdir(full_path):
                    copy_tree(
                        full_path, os.path.join(dest_extension_path, name)
                    )

        # Copy themes files
        all_themes = find_all_lab_theme()
        for theme in all_themes:
            theme_dst = os.path.join(
                dest_static_path, 'build', 'themes', theme[0]
            )
            copy_tree(theme[1], theme_dst)

    def start(self):

        if self.notebook_path:
            page_config = get_page_config(
                base_url=self.base_url, settings={}, log=None
            )
            page_config['themesUrl'] = url_path_join('build', 'themes')
            page_config['fullStaticUrl'] = url_path_join(
                self.base_url, 'build'
            )
            page_config['fullLabextensionsUrl'] = url_path_join(
                self.base_url, 'labextensions'
            )
            page_config['settingsUrl'] = url_path_join(
                page_config['fullStaticUrl'], 'schemas'
            )

            if self.voilite_configuration.theme == 'light':
                themeName = 'JupyterLab Light'
            elif self.voilite_configuration.theme == 'dark':
                themeName = 'JupyterLab Dark'
            else:
                themeName = self.voilite_configuration.theme
            page_config['labThemeName'] = themeName

            with open(self.notebook_path) as f:
                nb = nbformat.read(f, 4)
                src = [
                    {
                        'cell_source': cell['source'],
                        'cell_type': cell['cell_type'],
                    }
                    for cell in nb['cells']
                ]
                page_config['notebookSrc'] = src

            self.copy_static_files(page_config)
            voilite_converter = VoiliteExporter(
                voilite_config=self.voilite_configuration,
                page_config=page_config,
                base_url=self.base_url,
            )
            content, _ = voilite_converter.from_filename(self.notebook_path)
            with open(
                os.path.join(self.output_prefix, 'index.html'), 'w'
            ) as f:
                f.write(content)


main = Voilite.launch_instance
