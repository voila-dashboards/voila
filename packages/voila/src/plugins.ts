/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import { JupyterFrontEndPlugin } from '@jupyterlab/application';
import { pathsPlugin } from './voilaplugins/path';
import { translatorPlugin } from './voilaplugins/translator';
import { renderOutputsPlugin, widgetManager } from './voilaplugins/widget';

/**
 * Export the plugins as default.
 */
const plugins: JupyterFrontEndPlugin<any>[] = [
  pathsPlugin,
  translatorPlugin,
  widgetManager,
  renderOutputsPlugin
];

export default plugins;

export { pathsPlugin, translatorPlugin, widgetManager, renderOutputsPlugin };
