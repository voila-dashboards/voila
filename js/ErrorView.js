/***************************************************************************
* Copyright (c) 2018, Voila contributors                                   *
*                                                                          *
* Distributed under the terms of the BSD 3-Clause License.                 *
*                                                                          *
* The full license is in the file LICENSE, distributed with this software. *
****************************************************************************/

import { OutputAreaModel, OutputArea } from '@jupyterlab/outputarea';
import { createSimpleRenderMimeRegistry } from './renderMime'

// Output view for errors in callbacks
export class ErrorView {
    constructor(element) {
        this._element = element
        this._outputModel = new OutputAreaModel({trusted: true})
        this._outputView = new OutputArea({
            rendermime: createSimpleRenderMimeRegistry(),
            model: this._outputModel,
        })
        this._element.appendChild(this._outputView.node)
    }

    showError(errorContent) {
        const model = { ...errorContent, output_type: 'error' }
        this._outputModel.add(model)
    }
}
