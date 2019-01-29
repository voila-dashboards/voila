{# this template is rendered as response to an ajax call, and inserted into a div#}
{%- extends 'base.tpl' -%}
{%- block header -%}

<script type="text/javascript">
    // update the config data to have the right kernel id
    (function() {
        var el = document.getElementById("jupyter-config-data")
        var data = JSON.parse(el.innerHTML)
        data['kernelId'] = "{{resources.kernel_id}}"
        el.innerHTML = JSON.stringify(data)
    })()
</script>

{%- endblock header -%}

{% block body %}  {# no body tag, the the rest the same as in default voila.tpl #}
  <div tabindex="-1" id="notebook" class="border-box-sizing">
    <div class="container" id="notebook-container">
        {{ super() }}
    </div>
  </div>
{%- endblock body %}


{% block footer %}
{% block footer_js %}
<script>
requirejs(
    [
        "static/main",
    {% for ext in resources.nbextensions -%}
        "{{resources.base_url}}voila/nbextensions/{{ ext }}.js",
    {% endfor %}
    ]
)
</script>

{% endblock footer_js %}
{% endblock footer %}
