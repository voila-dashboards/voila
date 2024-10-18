import { IOutput } from '@jupyterlab/nbformat';
import { OutputAreaModel, SimplifiedOutputArea } from '@jupyterlab/outputarea';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Widget } from '@lumino/widgets';
import { PageConfig, URLExt } from '@jupyterlab/coreutils';
import { type VoilaWidgetManager } from '@voila-dashboards/widgets-manager8/lib/manager';

/**
 * Interface representing the structure of an execution result message.
 */
export interface IExecutionResultMessage {
  action: 'execution_result';
  payload: {
    output_cell: { outputs: IOutput[] };
    cell_index: number;
    total_cell: number;
  };
}

/**
 * Interface representing the structure of an execution error message.
 */
export interface IExecutionErrorMessage {
  action: 'execution_error';
  payload: {
    error: string;
  };
}

/**
 * Interface representing a received widget model
 * containing output and execution models.
 */
export interface IReceivedWidgetModel {
  [modelId: string]: {
    outputModel: OutputAreaModel;
    executionModel: IOutput;
  };
}
export type IExecutionMessage =
  | IExecutionResultMessage
  | IExecutionErrorMessage;

export function getExecutionURL(kernelId?: string): string {
  const wsUrl = PageConfig.getWsUrl();
  return URLExt.join(wsUrl, 'voila/execution', kernelId ?? '');
}

/**
 * Handles the execution result by rendering the output area and managing widget models.
 *
 * @param payload - The payload from the execution result message,
 *  including the output cell and cell index.
 * @param rendermime - A render mime registry to render the output.
 * @param widgetManager - The Voila widget manager to manage Jupyter widgets.
 * @returns An object containing a model ID and its corresponding output and
 * execution models if the model is not ready to be rendered, undefined otherwise.
 */
export function handleExecutionResult({
  payload,
  rendermime,
  widgetManager
}: {
  payload: IExecutionResultMessage['payload'];
  rendermime: IRenderMimeRegistry;
  widgetManager: VoilaWidgetManager;
}): IReceivedWidgetModel | undefined {
  const { cell_index, output_cell } = payload;
  const element = document.querySelector(`[cell-index="${cell_index + 1}"]`);
  if (element) {
    const skeleton = element
      .getElementsByClassName('voila-skeleton-container')
      .item(0);
    if (skeleton) {
      element.removeChild(skeleton);
    }
    const model = createOutputArea({ rendermime, parent: element });
    if (!output_cell.outputs) {
      return;
    }
    if (output_cell.outputs.length > 0) {
      element.lastElementChild?.classList.remove(
        'jp-mod-noOutputs',
        'jp-mod-noInput'
      );
    }
    const key = 'application/vnd.jupyter.widget-view+json';
    for (const outputData of output_cell.outputs) {
      const modelId = (outputData?.data as any)?.[key]?.model_id;
      if (modelId) {
        if (widgetManager.registeredModels.has(modelId)) {
          model.add(outputData);
        } else {
          return {
            [modelId]: {
              outputModel: model,
              executionModel: outputData
            }
          };
        }
      } else {
        model.add(outputData);
      }
    }
  }
}

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
}): OutputAreaModel {
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
  parent.lastElementChild?.appendChild(wrapper);
  area.node.classList.add('jp-Cell-outputArea');

  area.node.style.display = 'flex';
  area.node.style.flexDirection = 'column';

  Widget.attach(area, wrapper);
  return model;
}

export function createSkeleton(): void {
  const innerHtml = `<div class="voila-skeleton-post">
      <div class="voila-skeleton-avatar"></div>
      <div class="voila-skeleton-line"></div>
      <div class="voila-skeleton-line"></div>
    </div>`;
  const elements = document.querySelectorAll('[cell-index]');
  elements.forEach((it) => {
    const element = document.createElement('div');
    element.className = 'voila-skeleton-container';
    element.innerHTML = innerHtml;
    it.appendChild(element);
  });
}
