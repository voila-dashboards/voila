{%- extends 'base.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}

{# this overrides the default behaviour of directly starting the kernel and executing the notebook #}
{% block notebook_execute %}
{% endblock notebook_execute %}


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

<style>
a.anchor-link {
  display: none;
}
.highlight  {
  margin: 0.4em;
}
</style>

{{ mathjax() }}

  <!-- voila spinner -->
  <style type="text/css">
    #loading {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 75vh;
        color: var(--jp-content-font-color1);
        font-family: sans-serif;
    }
  </style>
{%- endblock html_head_css -%}

{%- block body -%}
{% if resources.theme == 'dark' %}
<body class="jp-Notebook theme-dark" data-base-url="{{resources.base_url}}voila/">
{% else %}
<body class="jp-Notebook theme-light" data-base-url="{{resources.base_url}}voila/">
{% endif %}
  <div id="loading">
    <h2><i class="fa fa-spinner fa-spin" style="font-size:36px;"></i> Running {{nb_title}}...</i></h2>
  </div>
{# from this point on, the kernel is started #}
{%- with kernel_id = kernel_start() -%}
  <script id="jupyter-config-data" type="application/json">
  {
      "baseUrl": "{{resources.base_url}}",
      "kernelId": "{{kernel_id}}"
  }
  </script>
  {# from this point on, nb.cells contains output of the executed cells #}
  {% do notebook_execute(nb, kernel_id) %}
    {{ super() }}
{% endwith %}
<script type="text/javascript">
    // remove the loading element
    (function() {
      var el = document.getElementById("loading")
      el.parentNode.removeChild(el)
    })()
</script>
</body>
{%- endblock body -%}

