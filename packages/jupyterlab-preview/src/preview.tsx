import { IWidgetTracker } from '@jupyterlab/apputils';
import {
  ABCWidgetFactory,
  DocumentRegistry,
  DocumentWidget
} from '@jupyterlab/docregistry';
import { INotebookModel } from '@jupyterlab/notebook';
import {
  IFrame,
  ReactWidget,
  refreshIcon,
  ToolbarButton
} from '@jupyterlab/ui-components';
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

const IFRAME_SANDBOX: IFrame.SandboxExceptions[] = [
  'allow-same-origin',
  'allow-scripts',
  'allow-downloads',
  'allow-modals'
];
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
      content: new IFrame({
        sandbox: IFRAME_SANDBOX
      })
    });
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

    this.content.url = getVoilaUrl(context.path);
    this.content.title.icon = voilaIcon;

    this._renderOnSave = renderOnSave ?? false;
    this._disableSandbox = false;
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

    const disableIFrameSandbox = ReactWidget.create(
      <label className="jp-VoilaPreview-renderOnSave">
        <input
          name="disableIFrameSandbox"
          type="checkbox"
          defaultChecked={this._disableSandbox}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            this._disableSandbox = event.target.checked;
            const iframe = this.content.node.querySelector('iframe');
            if (!iframe) {
              return;
            }
            if (this._disableSandbox) {
              iframe.removeAttribute('sandbox');
            } else {
              iframe.setAttribute('sandbox', IFRAME_SANDBOX.join(' '));
            }
            if (iframe.contentWindow) {
              iframe.contentWindow.location.reload();
            }
          }}
        />
        Disable IFrame Sandbox
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
    this.toolbar.addItem('disableIFrameSandbox', disableIFrameSandbox);
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
  private _disableSandbox: boolean;
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
