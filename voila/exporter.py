#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
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
