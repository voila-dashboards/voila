{%- extends 'base.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}

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

  <!-- voila spinner -->
  <style>
    #loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 75vh;
        color: var(--jp-content-font-color1);
        font-family: sans-serif;
    }

    .spinner {
      animation: rotation 2s infinite linear;
      transform-origin: 50% 50%;
    }

    .spinner-container {
      width: 10%;
    }

    @keyframes rotation {
      from {transform: rotate(0deg);}
      to   {transform: rotate(359deg);}
    }

    .voila-spinner-color1{
      fill:#268380;
    }

    .voila-spinner-color2{
      fill:#f8e14b;
    }
  </style>
{%- endblock html_head_css -%}

{%- block body -%}
{%- block body_header -%}
{% if resources.theme == 'dark' %}
<body class="jp-Notebook theme-dark" data-base-url="{{resources.base_url}}voila/">
{% else %}
<body class="jp-Notebook theme-light" data-base-url="{{resources.base_url}}voila/">
{% endif %}
  <div id="loading">
    <div class="spinner-container">
      <svg class="spinner" data-name="c1" version="1.1" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg" xmlns:cc="http://creativecommons.org/ns#" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><metadata><rdf:RDF><cc:Work rdf:about=""><dc:format>image/svg+xml</dc:format><dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage"/><dc:title>voila</dc:title></cc:Work></rdf:RDF></metadata><title>spin</title><path class="voila-spinner-color1" d="m250 405c-85.47 0-155-69.53-155-155s69.53-155 155-155 155 69.53 155 155-69.53 155-155 155zm0-275.5a120.5 120.5 0 1 0 120.5 120.5 120.6 120.6 0 0 0-120.5-120.5z"/><path class="voila-spinner-color2" d="m250 405c-85.47 0-155-69.53-155-155a17.26 17.26 0 1 1 34.51 0 120.6 120.6 0 0 0 120.5 120.5 17.26 17.26 0 1 1 0 34.51z"/></svg>
    </div>
    <h2 id="loading_text">Running {{nb_title}}...</h2>
  </div>
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

