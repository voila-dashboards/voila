/***************************************************************************
* Copyright (c) 2018, Voila contributors                                   *
*                                                                          *
* Distributed under the terms of the BSD 3-Clause License.                 *
*                                                                          *
* The full license is in the file LICENSE, distributed with this software. *
****************************************************************************/

import { Kernel, ServerConnection, KernelMessage } from '@jupyterlab/services'
import { PageConfig } from '@jupyterlab/coreutils';

import { WidgetManager } from './manager'
import { ErrorView } from './ErrorView'

import 'font-awesome/css/font-awesome.css'
import '@phosphor/widgets/style/index.css'
import './widgets.css'

export class WidgetApplication {
    constructor (loader) {
        this._loader = loader;
    }

    async renderWidgets() {
        const baseUrl = PageConfig.getBaseUrl();
        const kernelId = PageConfig.getOption('kernelId');
        const connectionInfo = ServerConnection.makeSettings({baseUrl});
        let kernel = await Kernel.connectTo(kernelId, connectionInfo);

        this._kernel = kernel;

        const manager = new WidgetManager(kernel, this._loader);

        const options = {
            msgType: 'custom_message',
            channel: 'shell'
        }

        const msg = KernelMessage.createShellMessage(options)
        const execution = kernel.sendShellMessage(msg, true)
        execution.onIOPub = (msg) => {
            // If we have a display message, display the widget.
            if (KernelMessage.isDisplayDataMsg(msg)) {
                let widgetData = msg.content.data['application/vnd.jupyter.widget-view+json'];
                if (widgetData !== undefined && widgetData.version_major === 2) {
                    let model = manager.get_model(widgetData.model_id);
                    if (model !== undefined) {
                        model.then(model => {
                            manager.display_model(msg, model);
                        });
                    }
                }
            }
            else if (KernelMessage.isErrorMsg(msg)) {
                // Show errors to help with debugging
                errorView.showError(msg.content)
            }
        }
    }

    async cleanWidgets() {
        // terminate kernel process
        this._kernel.shutdown()
    }
}
