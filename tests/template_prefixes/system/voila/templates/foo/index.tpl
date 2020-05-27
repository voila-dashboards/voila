{%- extends 'nbconvert/templates/foo/index.tpl' -%}
{% block nested %}
this is block base:nested in voila/foo/index.tpl
{{ super() }}
{% endblock %}
