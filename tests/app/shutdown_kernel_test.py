import re


async def test_shutdown_handler(http_server_client, base_url):
    response = await http_server_client.fetch(base_url)
    html_text = response.body.decode('utf-8')
    pattern = r"""kernelId": ["']([0-9a-zA-Z-]+)["']"""
    groups = re.findall(pattern, html_text)
    kernel_id = groups[0]
    shutdown_url = f'{base_url}voila/api/shutdown/{kernel_id}'
    shutdown_response = await http_server_client.fetch(shutdown_url, method='POST', body=b'')
    assert shutdown_response.code == 204
