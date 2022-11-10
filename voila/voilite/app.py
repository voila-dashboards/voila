import gettext
import json
import logging
import os
import shutil
from copy import deepcopy
from distutils.dir_util import copy_tree
from pathlib import Path
from typing import Dict
from typing import List as TypeList

import jinja2
import nbformat
from jupyter_core.paths import jupyter_path
from jupyter_server.config_manager import recursive_update
from jupyter_server.services.contents.largefilemanager import LargeFileManager
from jupyter_server.utils import url_path_join
from traitlets import List, Unicode, default
from traitlets.config.application import Application
from traitlets.config.loader import Config

from ..configuration import VoilaConfiguration
from ..paths import ROOT, collect_static_paths, collect_template_paths
from ..utils import find_all_lab_theme, get_page_config
from .exporter import VoiliteExporter
from .voilite_tree_exporter import VoiliteTreeExporter


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

    def setup_template_dirs(self):
        if self.voilite_configuration.template:
            template_name = self.voilite_configuration.template
            self.template_paths = collect_template_paths(
                ['voila', 'nbconvert'], template_name, prune=True
            )
            self.static_paths = collect_static_paths(
                ['voila', 'nbconvert'], template_name
            )
            conf_paths = [
                os.path.join(d, 'conf.json') for d in self.template_paths
            ]
            for p in conf_paths:
                # see if config file exists
                if os.path.exists(p):
                    # load the template-related config
                    with open(p) as json_file:
                        conf = json.load(json_file)
                    # update the overall config with it, preserving CLI config priority
                    if 'traitlet_configuration' in conf:
                        recursive_update(
                            conf['traitlet_configuration'],
                            self.voilite_configuration.config.VoilaConfiguration,
                        )
                        # pass merged config to overall Voilà config
                        self.voilite_configuration.config.VoilaConfiguration = Config(
                            conf['traitlet_configuration']
                        )

        self.jinja2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_paths),
            extensions=['jinja2.ext.i18n'],
            **{'autoescape': True},
        )
        nbui = gettext.translation(
            'nbui', localedir=os.path.join(ROOT, 'i18n'), fallback=True
        )
        self.jinja2_env.install_gettext_translations(nbui, newstyle=False)

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
        self.setup_template_dirs()

        self.contents_manager = LargeFileManager(parent=self)

    def copy_static_files(self, federated_extensions: TypeList[str]) -> None:

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

    def convert_notebook(
        self,
        nb_path: str,
        page_config: Dict,
        output_prefix: str,
        output_name: str = None,
    ) -> None:
        nb_name = output_name

        nb_path = Path(nb_path)
        if not nb_name:
            nb_name = f'{nb_path.stem}.html'

        page_config_copy = deepcopy(page_config)

        with open(nb_path) as f:
            nb = nbformat.read(f, 4)
            src = [
                {
                    'cell_source': cell['source'],
                    'cell_type': cell['cell_type'],
                }
                for cell in nb['cells']
            ]
            page_config_copy['notebookSrc'] = src

        voilite_exporter = VoiliteExporter(
            voilite_config=self.voilite_configuration,
            page_config=page_config_copy,
            base_url=self.base_url,
        )
        content, _ = voilite_exporter.from_filename(nb_path)
        output_dir = os.path.join(output_prefix, nb_path.parent)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, nb_name), 'w') as f:
            f.write(content)

    def convert_directory(self, page_config):

        tree_exporter = VoiliteTreeExporter(
            jinja2_env=self.jinja2_env,
            voilite_configuration=self.voilite_configuration,
            contents_manager=self.contents_manager,
            base_url=self.base_url,
        )
        nb_paths = tree_exporter.from_contents()
        for nb in nb_paths:
            self.convert_notebook(
                nb,
                page_config,
                os.path.join(self.output_prefix, 'voila', 'render'),
            )

    def start(self):
        page_config = get_page_config(
            base_url=self.base_url, settings={}, log=None
        )
        page_config['themesUrl'] = url_path_join('build', 'themes')
        page_config['fullStaticUrl'] = url_path_join(self.base_url, 'build')
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
        federated_extensions = page_config.get('federated_extensions', [])
        self.copy_static_files(federated_extensions)

        if self.notebook_path:
            self.convert_notebook(
                self.notebook_path,
                page_config,
                self.output_prefix,
                'index.html',
            )
        else:
            self.convert_directory(page_config)


main = Voilite.launch_instance
