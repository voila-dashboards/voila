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

import { IIterator, iter } from '@lumino/algorithm';

import { Widget } from '@lumino/widgets';

export type IShell = VoilaShell;

/**
 * A namespace for Shell statics
 */
export namespace IShell {
  /**
   * The areas of the application shell where widgets can reside.
   */
  export type Area = 'main';
}

/**
 * The application shell.
 */
export class VoilaShell extends Widget implements JupyterFrontEnd.IShell {
  constructor() {
    super();
    this.id = 'main';
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
    options?: DocumentRegistry.IOpenOptions,
  ): void {
    // no-op for now
    // TODO: support adding widgets to areas?
  }

  /**
   * The current widget in the shell's main area.
   */
  get currentWidget(): Widget | null {
    return null;
  }

  widgets(area: IShell.Area): IIterator<Widget> {
    return iter([]);
  }
}
