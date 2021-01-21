/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import { PageConfig, URLExt } from '@jupyterlab/coreutils';
import '../style/index.css';

export {
  RenderMimeRegistry,
  standardRendererFactories
} from '@jupyterlab/rendermime';

export { WidgetManager } from './manager';
export { connectKernel } from './kernel';
export { renderMathJax } from './mathjax';
