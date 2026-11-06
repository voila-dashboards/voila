"""Tests loading template of jinja2 templates"""

import json
import os

import pytest

from jinja2 import Environment, FileSystemLoader

from voila.paths import collect_paths

HERE = os.path.dirname(__file__)

ROOT_DIRS = [os.path.join(HERE, "user"), os.path.join(HERE, "system")]


def test_loader_default_nbconvert():
    paths = collect_paths(["nbconvert"], "default", root_dirs=ROOT_DIRS)
    loader = FileSystemLoader(paths)
    env = Environment(loader=loader)
    template = env.get_template("index.tpl")
    output = template.render()
    assert "this is block base:nested in nbconvert/default/index.tpl" in output


def test_loader_foo():
    paths = collect_paths(["voila", "nbconvert"], "foo", root_dirs=ROOT_DIRS)
    loader = FileSystemLoader(paths)
    env = Environment(loader=loader)
    template = env.get_template("index.tpl")
    output = template.render()
    assert "this is block base:nested in voila/default/index.tpl" in output
    assert "this is block base:nested in voila/foo/index.tpl" in output
    assert "this is block base:nested in nbconvert/foo/index.tpl" in output
    assert "this is block base:nested in nbconvert/default/index.tpl" not in output


def test_loader_bar_voila():
    paths = collect_paths(["voila", "nbconvert"], "bar", root_dirs=ROOT_DIRS)
    loader = FileSystemLoader(paths)
    env = Environment(loader=loader)
    template = env.get_template("index.tpl")
    output = template.render()
    assert "this is block base in nbconvert/bar/index.tpl" in output
    assert "this is block base in nbconvert/default/index.tpl" in output
    assert "this is block base:nested in voila/default/index.tpl" in output
    assert "this is block base:nested2 in nbconvert/default/index.tpl" in output
    assert "this is block common in nbconvert/bar/parent.tpl" in output


def test_loader_bar_nbconvert():
    paths = collect_paths(["nbconvert"], "bar", root_dirs=ROOT_DIRS)
    loader = FileSystemLoader(paths)
    env = Environment(loader=loader)
    template = env.get_template("index.tpl")
    output = template.render()
    assert "this is block base in nbconvert/bar/index.tpl" in output
    assert "this is block base in nbconvert/default/index.tpl" in output
    assert "this is block base:nested in nbconvert/default/index.tpl" in output
    assert "this is block base:nested2 in nbconvert/default/index.tpl" in output
    assert "this is block common in nbconvert/bar/parent.tpl" in output


@pytest.mark.parametrize(
    "parents", [{"custom": "custom"}, {"custom": "parent", "parent": "custom"}]
)
def test_loader_template_inheritance_cycle(tmp_path, parents):
    for name, parent in parents.items():
        directory = tmp_path / "voila" / "templates" / name
        directory.mkdir(parents=True)
        (directory / "conf.json").write_text(json.dumps({"base_template": parent}))

    with pytest.raises(ValueError, match="Template inheritance cycle.*custom"):
        collect_paths(["voila"], "custom", root_dirs=[str(tmp_path)])
