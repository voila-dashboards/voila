/***************************************************************************
 * Copyright (c) 2023, Voilà contributors                                   *
 * Copyright (c) 2023, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { FilterFileBrowserModel } from '@jupyterlab/filebrowser';
import { DocumentManager } from '@jupyterlab/docmanager';

import { DocumentRegistry } from '@jupyterlab/docregistry';
import { VoilaFileBrowser } from './browser';
/**
 * The voila file browser provider.
 */
export const treeWidgetPlugin: JupyterFrontEndPlugin<void> = {
  id: '@voila-dashboards/voila:tree-widget',
  description: 'Provides the file browser.',
  activate: (app: JupyterFrontEnd): void => {
    const docRegistry = new DocumentRegistry();
    const docManager = new DocumentManager({
      registry: docRegistry,
      manager: app.serviceManager,
      opener
    });
    const fbModel = new FilterFileBrowserModel({
      manager: docManager,
      refreshInterval: 2147483646
    });
    const fb = new VoilaFileBrowser({
      id: 'filebrowser',
      model: fbModel
    });
    fb.showFileCheckboxes = false;
    fb.showLastModifiedColumn = false;
    app.shell.add(fb, 'main');
  },
  autoStart: true
};
