{%- extends 'default/index.tpl' -%}
{% block base %}
this is block base in nbconvert/bar/index.tpl
{{ super() }}
{% block nested %}
{{ super() }}
{% endblock %}
{% endblock %}
