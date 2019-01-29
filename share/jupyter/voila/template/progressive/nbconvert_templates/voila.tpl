{%- extends 'base.tpl' -%}

{%- block header -%}
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
  
{%- endblock header -%}


{%- block body -%}
{{ super() }}
</body>
{%- endblock body %}

