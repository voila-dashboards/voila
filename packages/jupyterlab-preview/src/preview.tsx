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

    const { getVoilaUrl, context, renderOnSave } = options;

    const trusted = VoilaPreview.checkTrustStatus(context.model.cells);
    if (trusted) {
      this.content.url = getVoilaUrl(context.path);
    } else {
      const accept = showDialog({
        title: 'Untrusted notebook detected',
        hasClose: false,
        body: 'The notebook is not trusted, do you want to render it?\nYou can trust this notebook by running the "Trust Notebook" command from the command palette.',
        buttons: [Dialog.cancelButton(), Dialog.okButton()]
      });
      accept
        .then((result) => {
          if (result.button.accept) {
            this.content.url = getVoilaUrl(context.path);
          } else {
            this.dispose();
          }
        })
        .catch(() => {
          this.dispose();
        });
    }
    this.content.title.icon = voilaIcon;

    this._renderOnSave = renderOnSave ?? false;

    context.pathChanged.connect(() => {
      this.content.url = getVoilaUrl(context.path);
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

    if (context) {
      this.toolbar.addItem('renderOnSave', renderOnSaveCheckbox);
      void context.ready.then(() => {
        context.fileChanged.connect(() => {
          if (this.renderOnSave) {
            this.reload();
          }
        });
      });
    }
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

  private _renderOnSave: boolean;
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

  export function checkTrustStatus(cells: CellList): boolean {
    for (let i = 0; i < cells.length; i++) {
      const cell = cells.get(i);
      if (cell.type === 'code' && cell.getMetadata('trusted') === false) {
        return false;
      }
    }
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
