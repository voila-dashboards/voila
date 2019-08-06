{%- extends 'lab.tpl' -%}


 {%- block output_group -%}
<script type="application/x.voila-lab-output+json">
{{ '{' }}
    {%- if not resources.global_content_filter.include_output_prompt -%}
    "showPrompt": false,
    {%- endif -%}
    "outputs": {{ cell.outputs | tojson }}
{{ '}' }}
</script>
{%- endblock output_group -%}
