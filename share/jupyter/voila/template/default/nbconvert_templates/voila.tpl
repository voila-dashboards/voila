
{%- extends 'base.tpl' -%}

{%- block header -%}
{%- endblock header -%}

{% block body %}
    <script id="jupyter-config-data" type="application/json">
    {
        "baseUrl": "{{server_root}}",
        "kernelId": "{{resources.kernel_id}}"
    }
    </script>
    <script type="text/javascript">
    // remove the loading element
    (function() {
      var el = document.getElementById("loading")
      el.parentNode.removeChild(el)
    })()
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
      padding: 20px;
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


    <div tabindex="-1" id="notebook" class="border-box-sizing">
        <div class="container" id="notebook-container">
            {{ super() }}
        </div>
    </div>
</body>

{%- endblock body %}





