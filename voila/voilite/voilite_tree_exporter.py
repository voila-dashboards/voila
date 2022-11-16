import os
from typing import Dict, List, Tuple

import jinja2
from jupyter_server.services.contents.largefilemanager import LargeFileManager
from jupyter_server.utils import url_path_join, url_escape
from ..configuration import VoilaConfiguration
from ..utils import find_all_lab_theme, create_include_assets_functions
from copy import deepcopy


class VoiliteTreeExporter:
    def __init__(
        self,
        jinja2_env: jinja2.Environment,
        voilite_configuration: VoilaConfiguration,
        contents_manager: LargeFileManager,
        base_url: str,
        page_config: Dict,
        output_prefix: str = '_output',
        **kwargs,
    ):

        self.jinja2_env = jinja2_env
        self.base_url = base_url
        self.contents_manager = contents_manager
        self.theme = voilite_configuration.theme
        self.template_name = voilite_configuration.template

        self.allowed_extensions = list(
            voilite_configuration.extension_language_mapping.keys()
        ) + ['.ipynb']
        self.output_prefix = output_prefix
        self.notebook_paths = []

        self.page_config = self.filter_extensions(page_config)

    def filter_extensions(self, page_config: Dict) -> Dict:

        page_config_copy = deepcopy(page_config)
        all_themes = find_all_lab_theme()
        all_theme_name = [x[0] for x in all_themes]
        filtered_extension = list(
            filter(
                lambda x: x['name'] in all_theme_name,
                page_config_copy['federated_extensions'],
            )
        )
        page_config_copy['federated_extensions'] = filtered_extension
        return page_config_copy

    def allowed_content(self, content: Dict) -> bool:
        if content['type'] == 'notebook':
            return True
        if content['type'] == 'directory' and content['name'] != '_output':
            return True
        __, ext = os.path.splitext(content.get('path'))
        return ext in self.allowed_extensions

    def from_contents(self, **kwargs) -> Tuple[str, List[str]]:

        self.resources = self.init_resources(**kwargs)
        self.template = self.jinja2_env.get_template('tree.html')

        return self.write_contents()

    def generate_breadcrumbs(self, path: str) -> List:
        breadcrumbs = [(url_path_join(self.base_url, 'voila/tree'), '')]
        parts = path.split('/')
        for i in range(len(parts)):
            if parts[i]:
                link = url_path_join(
                    self.base_url,
                    'voila/tree',
                    url_escape(url_path_join(*parts[: i + 1])),
                )
                breadcrumbs.append((link, parts[i]))
        return breadcrumbs

    def generate_page_title(self, path: str) -> str:
        parts = path.split('/')
        if len(parts) > 3:  # not too many parts
            parts = parts[-2:]
        page_title = url_path_join(*parts)
        if page_title:
            return page_title + '/'
        else:
            return 'Voilà Home'

    def write_contents(self, path='') -> Tuple[Dict, List[str]]:
        cm = self.contents_manager
        if cm.dir_exists(path=path):
            if cm.is_hidden(path) and not cm.allow_hidden:
                print('Refusing to serve hidden directory, via 404 Error')
                return

            breadcrumbs = self.generate_breadcrumbs(path)
            page_title = self.generate_page_title(path)
            contents = cm.get(path)

            contents['content'] = sorted(
                contents['content'], key=lambda i: i['name']
            )
            contents['content'] = list(
                filter(self.allowed_content, contents['content'])
            )

            for file in contents['content']:
                if file['type'] == 'notebook':
                    self.notebook_paths.append(file['path'])
                    file['path'] = file['path'].replace('.ipynb', '.html')
                elif file['type'] == 'directory':
                    self.write_contents(file['path'])

            page_content = self.template.render(
                contents=contents,
                page_title=page_title,
                breadcrumbs=breadcrumbs,
                **self.resources,
            )

            output_dir = os.path.join(
                self.output_prefix, 'voila', 'tree', path
            )
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, 'index.html'), 'w') as f:
                f.write(page_content)

            if path == '':
                with open(
                    os.path.join(self.output_prefix, 'index.html'), 'w'
                ) as f:
                    f.write(page_content)

        return self.notebook_paths

    def init_resources(self, **kwargs) -> Dict:

        resources = {
            'base_url': self.base_url,
            'page_config': self.page_config,
            'frontend': 'voilite',
            'theme': self.theme,
            'include_css': lambda x: '',
            'include_js': lambda x: '',
            'include_url': lambda x: '',
            'include_lab_theme': lambda x: '',
            **kwargs,
        }
        if self.page_config['labThemeName'] in [
            'JupyterLab Light',
            'JupyterLab Dark',
        ]:
            include_assets_functions = create_include_assets_functions(
                self.template_name, self.base_url
            )
            resources.update(include_assets_functions)

        return resources
