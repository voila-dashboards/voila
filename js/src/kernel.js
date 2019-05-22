import { Kernel, ServerConnection } from '@jupyterlab/services'
import { PageConfig } from '@jupyterlab/coreutils';

export
async function connectKernel(baseUrl, kernelId) {
    baseUrl = baseUrl || PageConfig.getBaseUrl();
    kernelId = kernelId || PageConfig.getOption('kernelId');
    const connectionInfo = ServerConnection.makeSettings({ baseUrl });

    let model = await Kernel.findById(kernelId, connectionInfo);
    let kernel = await Kernel.connectTo(model, connectionInfo);
    return kernel;
}
