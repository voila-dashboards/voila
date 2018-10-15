{%- extends 'basic.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}

{%- block header -%}
<!DOCTYPE html>
<html>
<head>
{%- block html_head -%}
<meta charset="utf-8" />
{% set nb_title = nb.metadata.get('title', '') or resources['metadata']['name'] %}
<title>Voila: {{nb_title}}</title>

<link rel="stylesheet" href="https://unpkg.com/font-awesome@4.5.0/css/font-awesome.min.css" type="text/css" />

<script
    data-main="{{resources.base_url}}voila/static/main"
    data-jupyter-kernel-id="{{resources.kernel_id}}"
    src="{{resources.base_url}}voila/static/require.min.js"
    integrity="sha256-Ae2Vz/4ePdIu6ZyI/5ZGsYnb+m0JlOmKPjt6XZ9JJkA="
    crossorigin="anonymous">
</script>

<script src="{{resources.base_url}}voila/static/jquery.min.js"></script>
<script>requirejs.config({ baseUrl: '{{resources.base_url}}voila/static' })</script>

<script id="jupyter-config-data" type="application/json">
{
    "baseUrl": "{{resources.base_url}}",
    "kernelId": "{{resources.kernel_id}}"
}
</script>

{% for css in resources.inlining.css -%}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<style type="text/css">
/* Overrides of notebook CSS for static HTML export */
body {
  overflow: visible;
  padding: 8px;
}

div#notebook {
  overflow: visible;
  border-top: none;
}

{%- if resources.global_content_filter.no_prompt-%}
div#notebook-container{
  padding: 6ex 12ex 8ex 12ex;
}
{%- endif -%}

@media print {
  div.cell {
    display: block;
    page-break-inside: avoid;
  }
  div.output_wrapper {
    display: block;
    page-break-inside: avoid;
  }
  div.output {
    display: block;
    page-break-inside: avoid;
  }
}
</style>

<!-- Custom stylesheet, it must be in the same directory as the html file -->
<!-- <link rel="stylesheet" href="custom.css"> -->

<!-- Loading mathjax macro -->
{{ mathjax() }}
{%- endblock html_head -%}
</head>
{%- endblock header -%}

{% block body %}
<body>
  <div tabindex="-1" id="notebook" class="border-box-sizing">
    <div class="container" id="notebook-container">
{{ super() }}
    </div>
  </div>
</body>
{%- endblock body %}

{% block footer %}
{{ super() }}
</html>
{% endblock footer %}
