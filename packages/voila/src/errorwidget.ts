import * as widgets from '@jupyter-widgets/base';

// Create a Widget Model that captures an error object
export function createErrorWidget(error: string): any {
  class ErrorWidget extends widgets.DOMWidgetModel {
    constructor(attributes?: any, options?: any) {
      attributes = {
        ...attributes,
        _view_name: 'ErrorWidgetView',
        _view_module: 'voila-errorwidget',
        _model_module_version: '1.0.0',
        _view_module_version: '1.0.0',
        failed_module: attributes._view_module,
        failed_model_name: attributes._model_name,
        error: error
      };
      super(attributes, options);
    }
  }
  return ErrorWidget as any;
}

export class ErrorWidgetView extends widgets.DOMWidgetView {
  render() {
    const module = this.model.get('failed_module');
    const name = this.model.get('failed_model_name');
    const error = String(this.model.get('error').stack);
    this.el.innerHTML = `Failed to load widget '${name}' from module '${module}', error:<pre>${error}</pre>`;
  }
}
