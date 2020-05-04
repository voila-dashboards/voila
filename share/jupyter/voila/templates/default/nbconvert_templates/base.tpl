{%- extends 'lab.tpl' -%}

{%- block header -%}
<!DOCTYPE html>
<html>
<head>
{%- block html_head -%}
<meta charset="utf-8" />
{% set nb_title = nb.metadata.get('title', '') or resources['metadata']['name'] %}
<title>Voila: {{nb_title}}</title>

<link rel="stylesheet" href="https://unpkg.com/font-awesome@4.5.0/css/font-awesome.min.css" type="text/css" />

{%- block html_head_js -%}
<script
    src="{{resources.base_url}}static/voila/require.min.js"
    integrity="sha256-Ae2Vz/4ePdIu6ZyI/5ZGsYnb+m0JlOmKPjt6XZ9JJkA="
    crossorigin="anonymous">
</script>

{% block notebook_execute %}
    {%- set kernel_id = kernel_start() -%}
    <script id="jupyter-config-data" type="application/json">
    {
        "baseUrl": "{{resources.base_url}}",
        "kernelId": "{{kernel_id}}"
    }
    </script>
    {# from this point on, nb.cells contains output of the executed cells #}
    {% do notebook_execute(nb, kernel_id) %}
{%- endblock notebook_execute -%}

{%- endblock html_head_js -%}

{%- block html_head_css -%}
  <style>
    /*Hide empty cells*/
    .jp-mod-noOutputs.jp-mod-noInput {
      display: none;
    }
  </style>
{%- endblock html_head_css -%}
{%- endblock html_head -%}
</head>
{%- endblock header -%}

{% block footer %}
{% block footer_js %}
<script>
requirejs.config({ baseUrl: '{{resources.base_url}}static/voila/', waitSeconds: 30})
requirejs(
    [
        "main",
    {% for ext in resources.nbextensions -%}
        "{{resources.base_url}}static/voila/nbextensions/{{ ext }}.js",
    {% endfor %}
    ]
)
</script>

{% endblock footer_js %}
{{ super() }}
</html>
{% endblock footer %}
