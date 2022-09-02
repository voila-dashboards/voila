/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import { WidgetRenderer, output } from '@jupyter-widgets/jupyterlab-manager';

import { KernelWidgetManager } from '@jupyter-widgets/jupyterlab-manager';

import * as base from '@jupyter-widgets/base';

import * as controls from '@jupyter-widgets/controls';

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import * as LuminoWidget from '@lumino/widgets';

import { MessageLoop } from '@lumino/messaging';

import { Widget } from '@lumino/widgets';

import { Kernel } from '@jupyterlab/services';

import { OutputModel } from './output';

const WIDGET_MIMETYPE = 'application/vnd.jupyter.widget-view+json';

/**
 * A custom widget manager to render widgets with Voila
 */
export class WidgetManager extends KernelWidgetManager {
  constructor(
    kernel: Kernel.IKernelConnection,
    rendermime: IRenderMimeRegistry
  ) {
    super(kernel, rendermime);
    rendermime.addFactory(
      {
        safe: false,
        mimeTypes: [WIDGET_MIMETYPE],
        createRenderer: options => new WidgetRenderer(options, this as any)
      },
      1
    );
    this._registerWidgets();
  }

  async build_widgets(): Promise<void> {
    const tags = document.body.querySelectorAll(
      `script[type="${WIDGET_MIMETYPE}"]`
    );

    tags.forEach(async viewtag => {
      if (!viewtag?.parentElement) {
        return;
      }
      try {
        const widgetViewObject = JSON.parse(viewtag.innerHTML);
        const { model_id } = widgetViewObject;
        const model = await this.get_model(model_id);
        const widgetel = document.createElement('div');
        viewtag.parentElement.insertBefore(widgetel, viewtag);
        const view = await this.create_view(model);
        this.display_view(view, widgetel);
      } catch (error) {
        // Each widget view tag rendering is wrapped with a try-catch statement.
        //
        // This fixes issues with widget models that are explicitly "closed"
        // but are still referred to in a previous cell output.
        // Without the try-catch statement, this error interrupts the loop and
        // prevents the rendering of further cells.
        //
        // This workaround may not be necessary anymore with templates that make use
        // of progressive rendering.
        console.error(error);
      }
    });
  }

  async display_view(
    view: base.DOMWidgetView,
    el: HTMLElement
  ): Promise<Widget> {
    if (el) {
      LuminoWidget.Widget.attach(view.luminoWidget, el);
    }
    if (view.el) {
      view.el.setAttribute('data-voila-jupyter-widget', '');
      view.el.addEventListener('jupyterWidgetResize', (e: Event) => {
        MessageLoop.postMessage(
          view.luminoWidget,
          LuminoWidget.Widget.ResizeMessage.UnknownSize
        );
      });
    }
    return view.luminoWidget;
  }

  private _registerWidgets(): void {
    this.register({
      name: '@jupyter-widgets/base',
      version: base.JUPYTER_WIDGETS_VERSION,
      exports: base as any
    });
    this.register({
      name: '@jupyter-widgets/controls',
      version: controls.JUPYTER_CONTROLS_VERSION,
      exports: controls as any
    });
    this.register({
      name: '@jupyter-widgets/output',
      version: output.OUTPUT_WIDGET_VERSION,
      exports: {
        ...(output as any),
        OutputModel
      }
    });
  }
}
