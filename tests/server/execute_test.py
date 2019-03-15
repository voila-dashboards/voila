# test basics of voila running a notebook
import pytest
import tornado.web
import tornado.gen
import re
import json

try:
    from unittest import mock
except:
    import mock


@pytest.mark.gen_test
def test_hello_world(http_client, print_notebook_url):
    response = yield http_client.fetch(print_notebook_url)
    assert response.code == 200
    html_text = response.body.decode('utf-8')
    assert 'Hi Voila' in html_text
    assert 'gridstack.css' not in html_text, "gridstack should not be the default"
