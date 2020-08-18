Hi Voilà!
This is a test template, obviously

<link rel="stylesheet" type="text/css" href="test_template.css"></link>


List extensions:
{% for ext in resources.nbextensions -%}
    "{{resources.base_url}}voila/nbextensions/{{ ext }}.js",
{% endfor %}
