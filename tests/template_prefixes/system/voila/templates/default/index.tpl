{%- extends 'nbconvert/templates/default/index.tpl' -%}

{% block resources %}
for voila we want serve the files
Note that all template based on the default template will get this block!
Even when they are not a voila specific template (e.g. nbconvert/bar)
{% endblock resources %}

{% block nested %}
this is block base:nested in voila/default/index.tpl
{% endblock %}
