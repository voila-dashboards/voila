from typing import Dict, List, Set
from voila.utils import filter_extension


federated_extensions = [{"name": "foo"}, {"name": "bar"}, {"name": "foo-bar"}]


def list_to_set(inp: List[Dict]) -> Set:
    return set([x["name"] for x in inp])


def test_filter_extension():
    extensions = filter_extension(federated_extensions=federated_extensions)
    assert list_to_set(extensions) == list_to_set(federated_extensions)


def test_filter_extension_with_disabled():
    disabled_extensions = ["bar"]
    extensions = filter_extension(
        federated_extensions=federated_extensions,
        disabled_extensions=disabled_extensions,
    )
    assert list_to_set(extensions) == set(["foo", "foo-bar"])
