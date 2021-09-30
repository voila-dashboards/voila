// Copyright (c) Trung Le
// Distributed under the terms of the Modified BSD License.

import {
  DOMWidgetModel,
  DOMWidgetView,
  ISerializers
} from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from './version';

export class RenderErrorModel extends DOMWidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: RenderErrorModel.model_name,
      _model_module: MODULE_NAME,
      _model_module_version: MODULE_VERSION,
      _view_name: RenderErrorModel.view_name,
      _view_module: MODULE_NAME,
      _view_module_version: MODULE_VERSION,
      value: 'Hello World'
    };
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers
  };

  static model_name = 'RenderErrorModel';
  static view_name = 'RenderErrorView';
}

export class RenderErrorView extends DOMWidgetView {
  render(): void {
    this.el.classList.add('custom-widget');
    throw Error('Failed to render widget');
  }
}

export class ModuleErrorModel extends DOMWidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: ModuleErrorModel.model_name,
      _model_module: MODULE_NAME,
      _model_module_version: MODULE_VERSION,
      _view_name: ModuleErrorModel.view_name,
      _view_module: MODULE_NAME,
      _view_module_version: MODULE_VERSION,
      value: 'Hello World'
    };
  }

  initialize(): void {
    throw Error('Failed to initialize model.');
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers
  };

  static model_name = 'ModuleErrorModel';
  static view_name = 'ModuleErrorView';
}

export class ModuleErrorView extends DOMWidgetView {
  render(): void {
    this.el.classList.add('custom-widget');
    this.el.textContent = this.model.get('value');
  }
}
