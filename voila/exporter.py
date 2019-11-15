#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import mimetypes

import traitlets
from traitlets.config import Config

from jinja2 import contextfilter

from nbconvert.filters.markdown_mistune import IPythonRenderer, MarkdownWithMath
from nbconvert.exporters.html import HTMLExporter
from nbconvert.exporters.templateexporter import TemplateExporter
from nbconvert.filters.highlight import Highlight2HTML

from .threading import async_generator_to_thread

# As long as we support Python35, we use this library to get as async
# generators: https://pypi.org/project/async_generator/
from async_generator import async_generator, yield_


class VoilaMarkdownRenderer(IPythonRenderer):
    """Custom markdown renderer that inlines images"""

    def image(self, src, title, text):
        contents_manager = self.options['contents_manager']
        if contents_manager.file_exists(src):
            content = contents_manager.get(src, format='base64')
            data = content['content'].replace('\n', '')  # remove the newline
            mime_type, encoding = mimetypes.guess_type(src)
            src = 'data:{mime_type};base64,{data}'.format(mime_type=mime_type, data=data)
        return super(VoilaMarkdownRenderer, self).image(src, title, text)


class VoilaExporter(HTMLExporter):
    """Custom HTMLExporter that inlines the images using VoilaMarkdownRenderer"""

    markdown_renderer_class = traitlets.Type('mistune.Renderer').tag(config=True)

    # The voila exporter overrides the markdown renderer from the HTMLExporter
    # to inline images.
    @contextfilter
    def markdown2html(self, context, source):
        cell = context['cell']
        attachments = cell.get('attachments', {})
        cls = self.markdown_renderer_class
        renderer = cls(escape=False, attachments=attachments,
                       contents_manager=self.contents_manager,
                       anchor_link_text=self.anchor_link_text)
        return MarkdownWithMath(renderer=renderer).render(source)

    # The voila exporter disables the CSSHTMLHeaderPreprocessor from the HTMLExporter.

    @property
    def default_config(self):
        c = Config({
            'CSSHTMLHeaderPreprocessor': {
                'enabled': False
            },
            'VoilaExporter': {
                'markdown_renderer_class': 'voila.exporter.VoilaMarkdownRenderer'
            }
        })
        c.merge(super(VoilaExporter, self).default_config)
        return c

    # Instead, we use the VoilaCSSPreprocessor.

    @traitlets.default('preprocessors')
    def _default_preprocessors(self):
        return ['voila.csspreprocessor.VoilaCSSPreprocessor']

    # Overriding the default template file.

    @traitlets.default('template_file')
    def default_template_file(self):
        return 'voila.tpl'

    @async_generator
    async def generate_from_notebook_node(self, nb, resources=None, extra_context={}, **kw):
        # this replaces from_notebook_node, but calls template.generate instead of template.render
        langinfo = nb.metadata.get('language_info', {})
        lexer = langinfo.get('pygments_lexer', langinfo.get('name', None))
        highlight_code = self.filters.get('highlight_code', Highlight2HTML(pygments_lexer=lexer, parent=self))
        self.register_filter('highlight_code', highlight_code)

        # NOTE: we don't call HTML or TemplateExporter' from_notebook_node
        nb_copy, resources = super(TemplateExporter, self).from_notebook_node(nb, resources, **kw)
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
                'no_prompt': self.exclude_input_prompt and self.exclude_output_prompt,
                }

        # Jinja with Python3.5 does not support async (generators), which
        # means that it's not async all the way down. Which means that we
        # cannot use coroutines for the cell_generator, and that they will
        # block the IO loop. In that case we will run the iterator in a
        # thread instead.

        @async_generator_to_thread
        @async_generator
        async def async_jinja_generator():
            # Top level variables are passed to the template_exporter here.
            for output in self.template.generate(nb=nb_copy, resources=resources, **extra_context):
                await yield_((output, resources))

        async for output, resources in async_jinja_generator():
            await yield_((output, resources))

    @property
    def environment(self):
        env = super(type(self), self).environment
        if 'jinja2.ext.do' not in env.extensions:
            env.add_extension('jinja2.ext.do')
        return env
