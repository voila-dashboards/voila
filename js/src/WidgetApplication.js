/***************************************************************************
* Copyright (c) 2018, Voila contributors                                   *
*                                                                          *
* Distributed under the terms of the BSD 3-Clause License.                 *
*                                                                          *
* The full license is in the file LICENSE, distributed with this software. *
****************************************************************************/

import { Kernel, ServerConnection } from '@jupyterlab/services'
import { PageConfig } from '@jupyterlab/coreutils';

import { WidgetManager } from './manager';

import 'font-awesome/css/font-awesome.css'
import '@phosphor/widgets/style/index.css'
import '../css/widgets.css'

export class WidgetApplication {

    async renderWidgets() {
        const baseUrl = PageConfig.getBaseUrl();
        const kernelId = PageConfig.getOption('kernelId');
        const connectionInfo = ServerConnection.makeSettings({ baseUrl });

        let model = await Kernel.findById(kernelId, connectionInfo);
        let kernel = await Kernel.connectTo(model, connectionInfo);
        this._kernel = kernel;

        const widgetManager = new WidgetManager(kernel);
        widgetManager.build_widgets();
    }

    async cleanWidgets() {
        this._kernel.shutdown()
    }
}
