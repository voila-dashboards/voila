# test basics of Voilà running a notebook


async def test_hello_world(http_server_client, print_notebook_url):
    response = await http_server_client.fetch(print_notebook_url)
    assert response.code == 200
    html_text = response.body.decode("utf-8")
    assert "Hi Voilà" in html_text
    assert "print(" not in html_text, "by default the source code should be stripped"
    assert (
        "test_template.css" not in html_text
    ), "test_template should not be the default"
