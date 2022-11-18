#############################################################################
# Copyright (c) 2022, Voilà Contributors                                    #
# Copyright (c) 2022, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################


from copy import deepcopy

from jupyter_server.services.contents.largefilemanager import LargeFileManager
from nbconvert.exporters import TemplateExporter
from nbconvert.filters.highlight import Highlight2HTML
from nbconvert.preprocessors import ClearOutputPreprocessor
from traitlets import default

from ..exporter import VoilaExporter
from ..paths import collect_template_paths


class VoiliteExporter(VoilaExporter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('base_url', '/')
        kwargs.setdefault('contents_manager', LargeFileManager())

        super().__init__(*args, **kwargs)

        self.voilite_configuration = kwargs.get('voilite_config')
        self.page_config = kwargs.get('page_config', {})
        self.theme = self.voilite_configuration.theme
        self.template_name = self.voilite_configuration.template
        self.packages = kwargs.get('packages', [])
        self.nb_src = kwargs.get('nb_src', [])

        # TODO
        # Investigate why this doesnt work
        # jupyter nbconvert --to voilite_dashboard --VoilaConfiguration.strip_sources=False notebook.ipynb
        if self.voilite_configuration.strip_sources:
            self.exclude_input = True
            self.exclude_output_prompt = True
            self.exclude_input_prompt = True

    @default('template_paths')
    def _template_paths(self, prune=True, root_dirs=None):
        path = collect_template_paths(
            ['voila', 'nbconvert'], self.template_name, prune=True
        )
        return path

    def from_notebook_node(self, nb, resources=None, **kwargs):
        # this replaces from_notebook_node, but calls template.generate instead of template.render
        # Mocking the highligh_code filter

        langinfo = nb.metadata.get('language_info', {})
        lexer = langinfo.get('pygments_lexer', langinfo.get('name', None))
        highlight_code = self.filters.get(
            'highlight_code', Highlight2HTML(pygments_lexer=lexer, parent=self)
        )
        self.register_filter('highlight_code', highlight_code)
        # self.register_filter('highlight_code', lambda x: x)

        # TODO: This part is already copied three times across
        # nbconvert and Voila, we should do something about it
        nb_copy, resources = super(TemplateExporter, self).from_notebook_node(
            nb, resources, **kwargs
        )

        resources['base_url'] = self.base_url
        resources.setdefault('raw_mimetypes', self.raw_mimetypes)
        resources['global_content_filter'] = {
            'include_code': not self.exclude_code_cell,
            'include_markdown': not self.exclude_markdown,
            'include_raw': not self.exclude_raw,
            'include_unknown': not self.exclude_unknown,
            'include_input': not self.exclude_input,
            'include_output': not self.exclude_output,
            'include_input_prompt': not self.exclude_input_prompt,
            'include_output_prompt': not self.exclude_output_prompt,
            'no_prompt': self.exclude_input_prompt
            and self.exclude_output_prompt,
        }

        def notebook_execute(nb, kernel_id):
            return ''

        extra_context = dict(
            frontend='voilite',
            kernel_start=self.kernel_start,
            cell_generator=self.cell_generator,
            notebook_execute=notebook_execute,
        )

        html = []
        for html_snippet in self.template.generate(
            nb=nb_copy,
            resources=resources,
            **extra_context,
            static_url=self.static_url,
            page_config=self.update_page_config(self.page_config),
        ):
            html.append(html_snippet)

        return ''.join(html), resources

    def kernel_start(self, nb):
        return ''

    def cell_generator(self, nb, kernel_id):
        nb, _ = ClearOutputPreprocessor().preprocess(nb, {})
        for cell_idx, input_cell in enumerate(nb.cells):
            output = input_cell.copy()
            yield output

    def _init_resources(self, resources):
        resources = super()._init_resources(resources)
        # We are using the theme manager of JupyterLab instead of including
        # CSS file in the template.
        resources['include_css'] = lambda x: ''
        resources['include_lab_theme'] = lambda x: ''

        return resources

    def update_page_config(self, page_config):
        page_config_copy = deepcopy(page_config)

        page_config_copy['notebookSrc'] = self.nb_src
        if len(self.packages) > 0:
            packages_src = 'import piplite\n'
            packages_src += f'await piplite.install({self.packages})\n'
            page_config_copy['packagesSrc'] = packages_src

        return page_config_copy
