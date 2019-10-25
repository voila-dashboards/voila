{%- extends 'base.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}
{% import "spinner.tpl" as spinner %}

{# this overrides the default behaviour of directly starting the kernel and executing the notebook #}
{% block notebook_execute %}
{% endblock notebook_execute %}

{%- block html_head_css -%}
{{ super() }}

<link rel="stylesheet" type="text/css" href="{{resources.base_url}}voila/static/index.css">

{% if resources.theme == 'dark' %}
    <link rel="stylesheet" type="text/css" href="{{resources.base_url}}voila/static/theme-dark.css">
{% else %}
    <link rel="stylesheet" type="text/css" href="{{resources.base_url}}voila/static/theme-light.css">
{% endif %}

{% for css in resources.inlining.css %}
    <style>
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

{{ spinner.css() }}

{%- endblock html_head_css -%}

{%- block body -%}
{%- block body_header -%}
{% if resources.theme == 'dark' %}
<body class="jp-Notebook theme-dark" data-base-url="{{resources.base_url}}voila/">
{% else %}
<body class="jp-Notebook theme-light" data-base-url="{{resources.base_url}}voila/">
{% endif %}

{{ spinner.html() }}

<script>
var voila_process = function(cell_index, cell_count) {
  var el = document.getElementById("loading_text")
  el.innerHTML = `Executing ${cell_index} of ${cell_count}`
}
</script>

<div id="rendered_cells" style="display: none">
{%- endblock body_header -%}

{%- block body_loop -%}
{# from this point on, the kernel is started #}
{%- with kernel_id = kernel_start() -%}
  <script id="jupyter-config-data" type="application/json">
  {
      "baseUrl": "{{resources.base_url}}",
      "kernelId": "{{kernel_id}}"
  }
  </script>
  {% set cell_count = nb.cells|length %}
  {#
  Voila is using Jinja's Template.generate method to not render the whole template in one go.
  The current implementation of Jinja will however not yield template snippets if we call a blocks' super()
  Therefore it is important to have the cell loop in the template.
  The issue for Jinja is: https://github.com/pallets/jinja/issues/1044
  #}
  {%- for cell in cell_generator(nb, kernel_id) -%}
    {% set cellloop = loop %}
    {%- block any_cell scoped -%}
    <script>
      voila_process({{ cellloop.index }}, {{ cell_count }})
    </script>
      {{ super() }}
    {%- endblock any_cell -%}
  {%- endfor -%}
{% endwith %}
{%- endblock body_loop -%}

{%- block body_footer -%}
</div>

<script type="text/javascript">
    (function() {
      // remove the loading element
      var el = document.getElementById("loading")
      el.parentNode.removeChild(el)
      // show the cell output
      el = document.getElementById("rendered_cells")
      el.style.display = 'unset'
    })();
</script>
</body>
{%- endblock body_footer -%}
{%- endblock body -%}

