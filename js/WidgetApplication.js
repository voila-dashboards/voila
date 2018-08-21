
import { Kernel, ServerConnection, KernelMessage } from '@jupyterlab/services'

import { WidgetManager } from './manager'
import { ErrorView } from './ErrorView'

import 'font-awesome/css/font-awesome.css'
import '@phosphor/widgets/style/index.css'
import './widgets.css'


export class WidgetApplication {
    constructor (baseUrl, wsUrl, loader) {
        this._baseUrl = baseUrl
        this._wsUrl = wsUrl
        this._loader = loader
    }

    async renderWidgets() {
        let connectionInfo = ServerConnection.makeSettings({
            baseUrl : this._baseUrl,
            wsUrl : this._wsUrl
        });

        const kernelSpecs = await Kernel.getSpecs(connectionInfo)

        console.log(`Starting kernel ${kernelSpecs.default}`)

        const kernel = await Kernel.startNew({
            name: kernelSpecs.default,
            serverSettings: connectionInfo
        });

        this._kernel = kernel;

        const el = document.getElementById('ipywidget-server-result')
        const manager = new WidgetManager(kernel, el, this._loader);

        const errorEl = document.getElementById('ipywidget-server-errors')
        const errorView = new ErrorView(errorEl);
        manager.onError.connect((sender, msg) => errorView.showError(msg.content))

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
