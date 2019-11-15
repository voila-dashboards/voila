{%- extends 'display_priority.tpl' -%}

{% block codecell %}
{%- if not cell.outputs -%}
{%- set no_output_class="jp-mod-noOutputs" -%}
{%- endif -%}
{%- if not resources.global_content_filter.include_input -%}
{%- set no_input_class="jp-mod-noInput" -%}
{%- endif -%}
<div class="jp-Cell jp-CodeCell jp-Notebook-cell {{ no_output_class }} {{ no_input_class }}">
{{ super() }}
</div>
{%- endblock codecell %}

{% block input_group -%}
<div class="jp-Cell-inputWrapper">
<div class="jp-InputArea jp-Cell-inputArea">
{{ super() }}
</div>
</div>
{% endblock input_group %}

{% block input %}
<div class="jp-CodeMirrorEditor jp-Editor jp-InputArea-editor" data-type="inline">
     <div class="CodeMirror cm-s-jupyter">
{{ cell.source | highlight_code(metadata=cell.metadata) }}
     </div>
</div>
{%- endblock input %}

{% block output_group %}
<div class="jp-Cell-outputWrapper">
{{ super() }}
</div>
{% endblock output_group %}

{% block outputs %}
<div class="jp-OutputArea jp-Cell-outputArea">
{{ super() }}
</div>
{% endblock outputs %}

{% block in_prompt -%}
<div class="jp-InputPrompt jp-InputArea-prompt">
    {%- if cell.execution_count is defined -%}
        In&nbsp;[{{ cell.execution_count|replace(None, "&nbsp;") }}]:
    {%- else -%}
        In&nbsp;[&nbsp;]:
    {%- endif -%}
</div>
{%- endblock in_prompt %}

{% block empty_in_prompt -%}
<div class="jp-InputPrompt jp-InputArea-prompt">
</div>
{%- endblock empty_in_prompt %}

{#
  output_prompt doesn't do anything in HTML,
  because there is a prompt div in each output area (see output block)
 #}
{% block output_prompt %}
{% endblock output_prompt %}

{% block output_area_prompt %}
    <div class="jp-OutputPrompt jp-OutputArea-prompt">
{%- if output.output_type == 'execute_result' -%}
    {%- if cell.execution_count is defined -%}
        Out[{{ cell.execution_count|replace(None, "&nbsp;") }}]:
    {%- else -%}
        Out[&nbsp;]:
    {%- endif -%}
{%- endif -%}
    </div>
{% endblock output_area_prompt %}

{% block output %}
<div class="jp-OutputArea-child">
{% if resources.global_content_filter.include_output_prompt %}
    {{ self.output_area_prompt() }}
{% endif %}
{{ super() }}
</div>
{% endblock output %}

{% block markdowncell scoped %}
<div class="jp-Cell-inputWrapper">
{%- if resources.global_content_filter.include_input_prompt-%}
    {{ self.empty_in_prompt() }}
{%- endif -%}
<div class="jp-RenderedHTMLCommon jp-RenderedMarkdown jp-MarkdownOutput" data-mime-type="text/markdown">
{{ cell.source  | markdown2html | strip_files_prefix }}
</div>
</div>
{%- endblock markdowncell %}

{% block unknowncell scoped %}
unknown type  {{ cell.type }}
{% endblock unknowncell %}

{% block execute_result -%}
{%- set extra_class="jp-OutputArea-executeResult" -%}
{% block data_priority scoped %}
{{ super() }}
{% endblock data_priority %}
{%- set extra_class="" -%}
{%- endblock execute_result %}

{% block stream_stdout -%}
<div class="jp-RenderedText jp-OutputArea-output" data-mime-type="text/plain">
<pre>
{{- output.text | ansi2html -}}
</pre>
</div>
{%- endblock stream_stdout %}

{% block stream_stderr -%}
<div class="jp-RenderedText jp-OutputArea-output" data-mime-type="application/vnd.jupyter.stderr">
<pre>
{{- output.text | ansi2html -}}
</pre>
</div>
{%- endblock stream_stderr %}

{% block data_svg scoped -%}
<div class="jp-RenderedSVG jp-OutputArea-output {{ extra_class }}" data-mime-type="image/svg+xml">
{%- if output.svg_filename %}
<img src="{{ output.svg_filename | posix_path }}">
{%- else %}
{{ output.data['image/svg+xml'] }}
{%- endif %}
</div>
{%- endblock data_svg %}

{% block data_html scoped -%}
<div class="jp-RenderedHTMLCommon jp-RenderedHTML jp-OutputArea-output {{ extra_class }}" data-mime-type="text/html">
{{ output.data['text/html'] }}
</div>
{%- endblock data_html %}

{% block data_markdown scoped -%}
<div class="jp-RenderedHTMLCommon jp-RenderedMarkdown jp-OutputArea-output {{ extra_class }}" data-mime-type="text/markdown">
{{ output.data['text/markdown'] | markdown2html }}
</div>
{%- endblock data_markdown %}

{% block data_png scoped %}
<div class="jp-RenderedImage jp-OutputArea-output {{ extra_class }}">
{%- if 'image/png' in output.metadata.get('filenames', {}) %}
<img src="{{ output.metadata.filenames['image/png'] | posix_path }}"
{%- else %}
<img src="data:image/png;base64,{{ output.data['image/png'] }}"
{%- endif %}
{%- set width=output | get_metadata('width', 'image/png') -%}
{%- if width is not none %}
width={{ width }}
{%- endif %}
{%- set height=output | get_metadata('height', 'image/png') -%}
{%- if height is not none %}
height={{ height }}
{%- endif %}
{%- if output | get_metadata('unconfined', 'image/png') %}
class="unconfined"
{%- endif %}
>
</div>
{%- endblock data_png %}

{% block data_jpg scoped %}
<div class="jp-RenderedImage jp-OutputArea-output {{ extra_class }}">
{%- if 'image/jpeg' in output.metadata.get('filenames', {}) %}
<img src="{{ output.metadata.filenames['image/jpeg'] | posix_path }}"
{%- else %}
<img src="data:image/jpeg;base64,{{ output.data['image/jpeg'] }}"
{%- endif %}
{%- set width=output | get_metadata('width', 'image/jpeg') -%}
{%- if width is not none %}
width={{ width }}
{%- endif %}
{%- set height=output | get_metadata('height', 'image/jpeg') -%}
{%- if height is not none %}
height={{ height }}
{%- endif %}
{%- if output | get_metadata('unconfined', 'image/jpeg') %}
class="unconfined"
{%- endif %}
>
</div>
{%- endblock data_jpg %}

{% block data_latex scoped %}
<div class="jp-RenderedLatex jp-OutputArea-output {{ extra_class }}" data-mime-type="text/latex">
{{ output.data['text/latex'] }}
</div>
{%- endblock data_latex %}

{% block error -%}
<div class="jp-RenderedText jp-OutputArea-output" data-mime-type="application/vnd.jupyter.stderr">
<pre>
{{- super() -}}
</pre>
</div>
{%- endblock error %}

{%- block traceback_line %}
{{ line | ansi2html }}
{%- endblock traceback_line %}

{%- block data_text scoped %}
<div class="jp-RenderedText jp-OutputArea-output {{ extra_class }}" data-mime-type="text/plain">
<pre>
{{- output.data['text/plain'] | ansi2html -}}
</pre>
</div>
{%- endblock -%}

{#
 ###############################################################################
 # TODO: how to better handle JavaScript repr?                                 #
 ###############################################################################
 #}

{% set div_id = uuid4() %}
{%- block data_javascript scoped %}
<div id="{{ div_id }}"></div>
<div class="jp-RenderedJavaScript jp-OutputArea-output {{ extra_class }}" data-mime-type="application/javascript">
<script type="text/javascript">
{{ output.data['application/javascript'] }}
</script>
</div>
{%- endblock -%}

{%- block data_widget_state scoped %}
{% set div_id = uuid4() %}
{% set datatype_list = output.data | filter_data_type %}
{% set datatype = datatype_list[0]%}
<div id="{{ div_id }}"></div>
<div class="output_subarea output_widget_state {{ extra_class }}">
<script type="{{ datatype }}">
{{ output.data[datatype] | json_dumps }}
</script>
</div>
{%- endblock data_widget_state -%}

{%- block data_widget_view scoped %}
{% set div_id = uuid4() %}
{% set datatype_list = output.data | filter_data_type %}
{% set datatype = datatype_list[0]%}
<div id="{{ div_id }}"></div>
<div class="jupyter-widgets jp-OutputArea-output {{ extra_class }}">
<script type="{{ datatype }}">
{{ output.data[datatype] | json_dumps }}
</script>
</div>
{%- endblock data_widget_view -%}

{%- block footer %}
{% set mimetype = 'application/vnd.jupyter.widget-state+json'%}
{% if mimetype in nb.metadata.get("widgets",{})%}
<script type="{{ mimetype }}">
{{ nb.metadata.widgets[mimetype] | json_dumps }}
</script>
{% endif %}
{{ super() }}
{%- endblock footer-%}
