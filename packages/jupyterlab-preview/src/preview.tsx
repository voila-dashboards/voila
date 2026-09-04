import {
  IFrame,
  ToolbarButton,
  ReactWidget,
  IWidgetTracker,
  showDialog,
  Dialog
} from '@jupyterlab/apputils';
import {
  ABCWidgetFactory,
  DocumentRegistry,
  DocumentWidget
} from '@jupyterlab/docregistry';

import { CellList, INotebookModel } from '@jupyterlab/notebook';

import { refreshIcon } from '@jupyterlab/ui-components';

import { Token } from '@lumino/coreutils';

import { Signal } from '@lumino/signaling';

import * as React from 'react';

import { voilaIcon } from './icons';

/**
 * A class that tracks Voilà Preview widgets.
 */
export interface IVoilaPreviewTracker extends IWidgetTracker<VoilaPreview> {}

/**
 * The Voilà Preview tracker token.
 */
export const IVoilaPreviewTracker = new Token<IVoilaPreviewTracker>(
  '@voila-dashboards/jupyterlab-preview:IVoilaPreviewTracker'
);

/**
 * A DocumentWidget that shows a Voilà preview in an IFrame.
 */
export class VoilaPreview extends DocumentWidget<IFrame, INotebookModel> {
  /**
   * Instantiate a new VoilaPreview.
   * @param options The VoilaPreview instantiation options.
   */
  constructor(options: VoilaPreview.IOptions) {
    super({
      ...options,
      content: new IFrame()
    });
    const iframe = this.content.node.querySelector('iframe');
    if (iframe) {
      iframe.removeAttribute('sandbox');
    }

    window.onmessage = (event: any) => {
      //console.log("EVENT: ", event);
      const level = event?.data?.level;
      const msg = event?.data?.msg;
      if (!level || !msg) {
        return;
      }
      switch (level) {
        case 'debug':
          console.debug(msg);
          break;

        case 'info':
          console.info(msg);
          break;

        case 'warn':
          console.warn(msg);
          break;

        case 'error':
          console.error(msg);
          break;

        default:
          console.log(event);
          break;
      }
    };

    this.content.title.icon = voilaIcon;
    const { getVoilaUrl, context, renderOnSave } = options;

    this._renderOnSave = renderOnSave ?? false;
    this._getVoilaUrl = getVoilaUrl;
    void this._init(context).catch((e) => {
      console.error('Failed to initialize the Voila preview', e);
      this.dispose();
    });

    const reloadButton = new ToolbarButton({
      icon: refreshIcon,
      tooltip: 'Reload Preview',
      onClick: async () => {
        try {
          await context.save();
        } catch (e) {
          console.error(e);
        }
        this.reload();
      }
    });

    const renderOnSaveCheckbox = ReactWidget.create(
      <label className="jp-VoilaPreview-renderOnSave">
        <input
          name="renderOnSave"
          type="checkbox"
          defaultChecked={renderOnSave}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            this._renderOnSave = event.target.checked;
          }}
        />
        Render on Save
      </label>
    );

    this.toolbar.addItem('reload', reloadButton);

    this.toolbar.addItem('renderOnSave', renderOnSaveCheckbox);
  }

  /**
   * Dispose the preview widget.
   */
  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    super.dispose();
    Signal.clearData(this);
  }

  /**
   * Reload the preview.
   */
  reload(): void {
    const iframe = this.content.node.querySelector('iframe');
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.location.reload();
    }
  }

  /**
   * Get whether the preview reloads when the context is saved.
   */
  get renderOnSave(): boolean {
    return this._renderOnSave;
  }

  /**
   * Set whether the preview reloads when the context is saved.
   */
  set renderOnSave(renderOnSave: boolean) {
    this._renderOnSave = renderOnSave;
  }

  /**
   * Initialize the preview once the context is ready.
   *
   * @param context The document context.
   */
  private async _init(
    context: DocumentRegistry.IContext<INotebookModel>
  ): Promise<void> {
    await context.ready;

    if (!(await VoilaPreview.ensureTrusted(context))) {
      this.dispose();
      return;
    }

    context.fileChanged.connect(() => {
      if (this.renderOnSave) {
        this.reload();
      }
    });

    context.pathChanged.connect(() => {
      this.content.url = this._getVoilaUrl(context.path);
    });

    this.content.url = this._getVoilaUrl(context.path);
  }

  private _renderOnSave: boolean;
  private _getVoilaUrl: (path: string) => string;
}

/**
 * A namespace for VoilaPreview statics.
 */
export namespace VoilaPreview {
  /**
   * Instantiation options for `VoilaPreview`.
   */
  export interface IOptions
    extends DocumentWidget.IOptionsOptionalContent<IFrame, INotebookModel> {
    /**
     * The Voilà URL function.
     */
    getVoilaUrl: (path: string) => string;

    /**
     * Whether to reload the preview on context saved.
     */
    renderOnSave?: boolean;
  }

  /**
   * Mark every cell of a notebook as trusted and save it.
   *
   * @param context The document context.
   */
  export async function trustNotebook({
    context
  }: {
    context: DocumentRegistry.IContext<INotebookModel>;
  }): Promise<void> {
    for (const cell of context.model.cells) {
      cell.trusted = true;
    }
    await context.save();
  }

  /**
   * Whether every code cell of a notebook is trusted.
   *
   * A missing trust status is treated as untrusted, to match the behavior of
   * `CellModel`.
   *
   * @param cells The cells of the notebook.
   */
  export function checkTrustStatus(cells?: CellList): boolean {
    if (!cells) {
      return false;
    }
    for (const cell of cells) {
      if (cell.type === 'code' && !cell.trusted) {
        return false;
      }
    }
    return true;
  }

  /**
   * Make sure a notebook is trusted before Voila executes it, asking the user
   * for confirmation if it is not.
   *
   * @param context The document context.
   * @returns Whether the notebook may be rendered.
   */
  export async function ensureTrusted(
    context: DocumentRegistry.IContext<INotebookModel>
  ): Promise<boolean> {
    if (checkTrustStatus(context.model?.cells)) {
      return true;
    }

    const body = (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          maxWidth: '600px'
        }}
      >
        <span>
          It seems that you are rendering a notebook that you have received from
          a third party.
        </span>
        <span>
          Executing an untrusted Jupyter notebook may execute malicious code. If
          you trust the content of this document, you can select{' '}
          <b>Render anyway</b>, which will mark this notebook as trusted and run
          it.
        </span>
        <span>
          For more information, see{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://jupyter-server.readthedocs.io/en/stable/operators/security.html#security-in-notebook-documents"
          >
            the Jupyter security documentation
          </a>
          .
        </span>
      </div>
    );

    const result = await showDialog({
      title: 'Untrusted notebook detected',
      hasClose: false,
      body,
      buttons: [
        Dialog.cancelButton(),
        Dialog.okButton({ label: 'Render anyway' })
      ]
    });

    if (!result.button.accept) {
      return false;
    }

    await trustNotebook({ context });
    return true;
  }
}

export class VoilaPreviewFactory extends ABCWidgetFactory<
  VoilaPreview,
  INotebookModel
> {
  defaultRenderOnSave = false;

  constructor(
    private getVoilaUrl: (path: string) => string,
    options: DocumentRegistry.IWidgetFactoryOptions<VoilaPreview>
  ) {
    super(options);
  }

  protected createNewWidget(
    context: DocumentRegistry.IContext<INotebookModel>
  ): VoilaPreview {
    return new VoilaPreview({
      context,
      getVoilaUrl: this.getVoilaUrl,
      renderOnSave: this.defaultRenderOnSave
    });
  }
}
