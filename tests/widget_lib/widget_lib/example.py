#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Trung Le.
# Distributed under the terms of the Modified BSD License.

"""
TODO: Add module docstring
"""

from ipywidgets import DOMWidget, Button
from traitlets import Unicode
from ._frontend import module_name, module_version


class ViewRenderError(DOMWidget):
    _model_name = Unicode('RenderErrorModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode('RenderErrorView').tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    value = Unicode('Hello RenderError').tag(sync=True)


class ModelInitializationError(DOMWidget):
    _model_name = Unicode('ModuleErrorModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode('ModuleErrorView').tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    value = Unicode('Hello ModuleError').tag(sync=True)


class ModuleImportError(DOMWidget):
    _model_name = Unicode('ModuleImportErrorModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode('ModuleImportErrorView').tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)


class WrongVersion(Button):
    _model_module_version = Unicode('0.0').tag(sync=True)
