import {
  OutputArea,
  OutputAreaModel,
  SimplifiedOutputArea
} from '@jupyterlab/outputarea';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Kernel, KernelMessage } from '@jupyterlab/services';
import { JSONObject } from '@lumino/coreutils';
import { Widget } from '@lumino/widgets';

/**
 * Creates an output area model and attaches the output area to a specified parent element.
 *
 * @param rendermime - The render mime registry.
 * @param parent - The parent HTML element where the output area will be appended.
 * @returns The created OutputAreaModel.
 */
export function createOutputArea({
  rendermime,
  parent
}: {
  rendermime: IRenderMimeRegistry;
  parent: Element;
}): { model: OutputAreaModel; area: SimplifiedOutputArea } {
  const model = new OutputAreaModel({ trusted: true });
  const area = new SimplifiedOutputArea({
    model,
    rendermime
  });

  const wrapper = document.createElement('div');
  wrapper.classList.add('jp-Cell-outputWrapper');
  const collapser = document.createElement('div');
  collapser.classList.add(
    'jp-Collapser',
    'jp-OutputCollapser',
    'jp-Cell-outputCollapser'
  );
  wrapper.appendChild(collapser);
  parent.appendChild(wrapper);
  area.node.classList.add('jp-Cell-outputArea');

  area.node.style.display = 'flex';
  area.node.style.flexDirection = 'column';

  Widget.attach(area, wrapper);
  area.outputLengthChanged.connect((_, number) => {
    if (number) {
      parent.classList.remove('jp-mod-noOutputs');
    }
  });
  return { model, area };
}

export function createSkeleton(): void {
  const innerHtml = `<div class="voila-skeleton-post">
      <div class="voila-skeleton-avatar"></div>
      <div class="voila-skeleton-line"></div>
      <div class="voila-skeleton-line"></div>
    </div>`;
  const elements = document.querySelectorAll('[cell-index]');
  elements.forEach((it) => {
    const codeCell =
      it.getElementsByClassName('jp-CodeCell').item(0) ||
      it.getElementsByClassName('code_cell').item(0); // for classic template
    if (codeCell) {
      const element = document.createElement('div');
      element.className = 'voila-skeleton-container';
      element.innerHTML = innerHtml;
      it.appendChild(element);
    }
  });
}

export async function executeCode(
  code: string,
  output: OutputArea,
  kernel: Kernel.IKernelConnection | null | undefined,
  metadata?: JSONObject
): Promise<KernelMessage.IExecuteReplyMsg | undefined> {
  // Override the default for `stop_on_error`.
  let stopOnError = false;
  if (
    metadata &&
    Array.isArray(metadata.tags) &&
    metadata.tags.indexOf('raises-exception') !== -1
  ) {
    stopOnError = false;
  }
  const content: KernelMessage.IExecuteRequestMsg['content'] = {
    code,
    stop_on_error: stopOnError
  };

  if (!kernel) {
    throw new Error('Session has no kernel.');
  }
  const future = kernel.requestExecute(content, false, metadata);
  output.future = future;
  return future.done;
}
