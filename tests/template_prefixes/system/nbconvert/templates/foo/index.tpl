{%- extends 'default/index.tpl' -%}
{% block nested %}
this is block base:nested in nbconvert/foo/index.tpl
{{ super() }}
{% endblock %}
