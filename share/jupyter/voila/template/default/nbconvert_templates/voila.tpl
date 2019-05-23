{%- extends 'base.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}

{%- block html_head_css -%}
<link rel="stylesheet" type="text/css" href="{{resources.base_url}}voila/static/index.css"></link>

{% if resources.theme == 'dark' %}
    <link rel="stylesheet" type="text/css" href="{{resources.base_url}}voila/static/theme-dark.css"></link>
{% else %}
    <link rel="stylesheet" type="text/css" href="{{resources.base_url}}voila/static/theme-light.css"></link>
{% endif %}

{% for css in resources.inlining.css %}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<link rel="stylesheet" type="text/css" href="https://unpkg.com/@jupyter-widgets/controls@1.4.4/css/widgets-base.css"></link>
<link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor/widgets@1.6.0/style/index.css"></link>

<style>
a.anchor-link {
  display: none;
}
.highlight  {
  margin: 0.4em;
}
</style>

{{ mathjax() }}
{%- endblock html_head_css -%}

{%- block body -%}
<body class="jp-Notebook" data-base-url="{{resources.base_url}}voila/">
{{ super() }}
</body>
{%- endblock body -%}

