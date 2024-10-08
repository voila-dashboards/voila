/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import '../style/index.css';

export {
  RenderMimeRegistry,
  standardRendererFactories
} from '@jupyterlab/rendermime';

export { EditorLanguageRegistry } from '@jupyterlab/codemirror';

export { PageConfig } from '@jupyterlab/coreutils';

export { MathJaxTypesetter } from '@jupyterlab/mathjax-extension';

export { createMarkdownParser } from '@jupyterlab/markedparser-extension';

export { extendedRendererFactories } from './rendermime';
export { WidgetManager } from './manager';
export { connectKernel } from './kernel';
// This is a no-op, keeping this around for backward compat
export function renderMathJax() {}
