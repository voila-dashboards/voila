import mimetypes

import nbconvert.exporters.html
from jinja2 import contextfilter
from nbconvert.filters.markdown_mistune import IPythonRenderer, MarkdownWithMath


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


class HTMLExporter(nbconvert.exporters.html.HTMLExporter):
    """Custom HTMLExporter that inlines the images using VoilaMarkdownRenderer"""
    @contextfilter
    def markdown2html(self, context, source):
        cell = context['cell']
        attachments = cell.get('attachments', {})
        renderer = VoilaMarkdownRenderer(escape=False, attachments=attachments,
                                         contents_manager=self.contents_manager,
                                         anchor_link_text=self.anchor_link_text)
        return MarkdownWithMath(renderer=renderer).render(source)
