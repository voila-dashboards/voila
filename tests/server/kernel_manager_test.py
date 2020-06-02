import json


async def test_api_kernels_endpoint(http_server_client, print_notebook_url):
    # start a voila kernel
    await http_server_client.fetch(print_notebook_url)

    response = await http_server_client.fetch("/voila/api/kernels")
    assert response.code == 200

    kernels = json.loads(response.body)
    assert len(kernels) == 1
    assert "id" in kernels[0]
