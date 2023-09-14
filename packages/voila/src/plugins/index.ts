/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import { JupyterFrontEndPlugin } from '@jupyterlab/application';
import { pathsPlugin } from './path';
import { translatorPlugin } from './translator';
import { renderOutputsPlugin } from './outputs_rendering';
import { themePlugin, themesManagerPlugin } from './themes';

/**
 * Export the plugins as default.
 */
const plugins: JupyterFrontEndPlugin<any>[] = [
  pathsPlugin,
  translatorPlugin,
  renderOutputsPlugin,
  themesManagerPlugin,
  themePlugin
];

export default plugins;

export {
  pathsPlugin,
  translatorPlugin,
  renderOutputsPlugin,
  themesManagerPlugin,
  themePlugin
};
