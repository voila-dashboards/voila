/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import { JupyterFrontEnd } from '@jupyterlab/application';

import { DocumentRegistry } from '@jupyterlab/docregistry';

import { BoxLayout, Widget } from '@lumino/widgets';

export type IShell = VoilaShell;

/**
 * A namespace for Shell statics
 */
export namespace IShell {
  /**
   * The areas of the application shell where widgets can reside.
   */
  export type Area = 'top' | 'bottom' | 'main';
}

/**
 * The application shell.
 */
export class VoilaShell extends Widget implements JupyterFrontEnd.IShell {
  constructor() {
    super();
    this.id = 'main';
    const rootLayout = new BoxLayout();
    rootLayout.alignment = 'start';
    this.layout = rootLayout;
  }

  activateById(id: string): void {
    // no-op
  }

  /**
   * Add a widget to the application shell.
   *
   * @param widget - The widget being added.
   *
   * @param area - Optional region in the shell into which the widget should
   * be added.
   *
   */
  add(
    widget: Widget,
    area?: IShell.Area,
    options?: DocumentRegistry.IOpenOptions
  ): void {
    switch (area) {
      case 'top':
        Widget.attach(
          widget,
          this.node,
          this.node.firstElementChild as HTMLElement
        );
        break;
      case 'bottom':
        Widget.attach(widget, this.node);
        break;
      case 'main':
        (this.layout as BoxLayout).addWidget(widget);
        break;
      default:
        break;
    }
  }

  /**
   * The current widget in the shell's main area.
   */
  get currentWidget(): Widget | null {
    return null;
  }

  widgets(area: IShell.Area): IterableIterator<Widget> {
    return [][Symbol.iterator]();
  }
}
