import pytest
import tornado.web

from voila.static_file_handler import AllowListFileHandler


def make_handler(tmp_path, allowlist=[], denylist=[]):
    handler = AllowListFileHandler.__new__(AllowListFileHandler)
    handler.initialize(allowlist=allowlist, denylist=denylist, path=str(tmp_path))
    handler.root = str(tmp_path)
    return handler


def test_allowlisted_exact(tmp_path):
    handler = make_handler(tmp_path, allowlist=[r"file\.js"])
    result = handler.get_absolute_path(str(tmp_path), "file.js")
    assert result == str(tmp_path / "file.js")


def test_not_allowlisted_raises(tmp_path):
    handler = make_handler(tmp_path, allowlist=[r"file\.js"])
    with pytest.raises(tornado.web.HTTPError) as exc_info:
        handler.get_absolute_path(str(tmp_path), "other.js")
    assert exc_info.value.status_code == 403


@pytest.mark.parametrize("path", ["FILE.JS", "File.Js"])
def test_allowlist_case_insensitive(tmp_path, path):
    handler = make_handler(tmp_path, allowlist=[r"file\.js"])
    result = handler.get_absolute_path(str(tmp_path), path)
    assert result == str(tmp_path / path)


def test_denylist_case_insensitive(tmp_path):
    handler = make_handler(tmp_path, allowlist=[r".*"], denylist=[r"secret\.txt"])
    with pytest.raises(tornado.web.HTTPError) as exc_info:
        handler.get_absolute_path(str(tmp_path), "SECRET.TXT")
    assert exc_info.value.status_code == 403


def test_denylist_blocks_even_if_allowlisted(tmp_path):
    handler = make_handler(tmp_path, allowlist=[r".*"], denylist=[r"blocked\.js"])
    with pytest.raises(tornado.web.HTTPError) as exc_info:
        handler.get_absolute_path(str(tmp_path), "blocked.js")
    assert exc_info.value.status_code == 403
