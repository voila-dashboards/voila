/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import { JupyterFrontEndPlugin } from '@jupyterlab/application';
import { pathsPlugin } from './plugins/path';
import { translatorPlugin } from './plugins/translator';
import { renderOutputsPlugin } from './plugins/outputs';
import { themePlugin, themesManagerPlugin } from './plugins/themes';
import { renderOutputsProgressivelyPlugin } from './plugins/outputs/index';

/**
 * Export the plugins as default.
 */
const plugins: JupyterFrontEndPlugin<any>[] = [
  pathsPlugin,
  translatorPlugin,
  renderOutputsPlugin,
  renderOutputsProgressivelyPlugin,
  themesManagerPlugin,
  themePlugin
];

export default plugins;

export {
  pathsPlugin,
  translatorPlugin,
  renderOutputsPlugin,
  renderOutputsProgressivelyPlugin,
  themesManagerPlugin,
  themePlugin
};
