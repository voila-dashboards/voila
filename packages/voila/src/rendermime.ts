/***************************************************************************
 * Copyright (c) 2021, Voilà contributors                                   *
 * Copyright (c) 2021, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import {
  htmlRendererFactory,
  markdownRendererFactory,
  latexRendererFactory,
  svgRendererFactory,
  imageRendererFactory,
  textRendererFactory
} from '@jupyterlab/rendermime';

import { rendererFactory as javascriptRendererFactory } from '@jupyterlab/javascript-extension';
import { IRenderMime } from '@jupyterlab/rendermime-interfaces';

export const extendedRendererFactories: ReadonlyArray<IRenderMime.IRendererFactory> = [
  htmlRendererFactory,
  markdownRendererFactory,
  latexRendererFactory,
  svgRendererFactory,
  imageRendererFactory,
  javascriptRendererFactory,
  textRendererFactory
];
