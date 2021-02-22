/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import { PageConfig } from '@jupyterlab/coreutils';

import { Kernel, KernelManager, ServerConnection } from '@jupyterlab/services';

export async function connectKernel(
  baseUrl?: string,
  kernelId?: string
): Promise<Kernel.IKernelConnection | undefined> {
  baseUrl = baseUrl ?? PageConfig.getBaseUrl();
  kernelId = kernelId ?? PageConfig.getOption('kernelId');
  const serverSettings = ServerConnection.makeSettings({ baseUrl });

  const manager = new KernelManager({ standby: 'never', serverSettings });
  const model = await manager.findById(kernelId);
  if (!model) {
    return;
  }
  const kernel = manager.connectTo({ model });
  return kernel;
}
