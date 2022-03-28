/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import { PageConfig } from '@jupyterlab/coreutils';

import { Kernel, KernelAPI, ServerConnection } from '@jupyterlab/services';

import { KernelConnection } from '@jupyterlab/services/lib/kernel/default';

export async function connectKernel(
  baseUrl?: string,
  kernelId?: string,
  options?: Partial<ServerConnection.ISettings>
): Promise<Kernel.IKernelConnection | undefined> {
  baseUrl = baseUrl ?? PageConfig.getBaseUrl();
  kernelId = kernelId ?? PageConfig.getOption('kernelId');
  const serverSettings = ServerConnection.makeSettings({ baseUrl, ...options });

  const model = await KernelAPI.getKernelModel(kernelId, serverSettings);
  if (!model) {
    return;
  }
  const kernel = new KernelConnection({ model, serverSettings });
  return kernel;
}
