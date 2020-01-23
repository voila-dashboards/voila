import {
  IFrame,
  MainAreaWidget,
  ToolbarButton,
  ReactWidget,
  IWidgetTracker
} from "@jupyterlab/apputils";

import { DocumentRegistry } from "@jupyterlab/docregistry";

import { INotebookModel } from "@jupyterlab/notebook";

import { Token } from "@phosphor/coreutils";

import { Signal } from "@phosphor/signaling";

import * as React from "react";

/**
 * A class that tracks Voila Preview widgets.
 */
export interface IVoilaPreviewTracker extends IWidgetTracker<VoilaPreview> {}

/**
 * The Voila Preview tracker token.
 */
export const IVoilaPreviewTracker = new Token<IVoilaPreviewTracker>(
  "@jupyter-voila/jupyterlab-preview:IVoilaPreviewTracker"
);

/**
 * The class name for a Voila preview icon.
 */
export const VOILA_ICON_CLASS = "jp-MaterialIcon jp-VoilaIcon";

/**
 * A MainAreaWidget that shows a Voila preview in an IFrame.
 */
export class VoilaPreview extends MainAreaWidget<IFrame> {
  /**
   * Instantiate a new VoilaPreview.
   * @param options The VoilaPreview instantiation options.
   */
  constructor(options: VoilaPreview.IOptions) {
    super({
      ...options,
      content: new IFrame({ sandbox: ["allow-same-origin", "allow-scripts"] })
    });

    const { url, label, context, renderOnSave } = options;

    this.content.url = url;
    this.content.title.label = label;
    this.content.title.icon = VOILA_ICON_CLASS;
    this.content.id = `voila-preview-${++Private.count}`;

    this.renderOnSave = renderOnSave;

    const reloadButton = new ToolbarButton({
      iconClassName: "jp-RefreshIcon",
      tooltip: "Reload Preview",
      onClick: () => {
        this.reload();
      }
    });

    const renderOnSaveCheckbox = ReactWidget.create(
      <label className="jp-VoilaPreview-renderOnSave">
        <input
          style={{ verticalAlign: "middle" }}
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

    this.toolbar.addItem("reload", reloadButton);
    this.toolbar.addItem("renderOnSave", renderOnSaveCheckbox);

    void context.ready.then(() => {
      context.fileChanged.connect(() => {
        if (this.renderOnSave) {
          this.reload();
        }
      });
    });
  }

  /**
   * Dispose the preview widget.
   */
  dispose() {
    if (this.isDisposed) {
      return;
    }
    Signal.clearData(this);
    super.dispose();
  }

  /**
   * Reload the preview.
   */
  reload() {
    const iframe = this.content.node.querySelector("iframe")!;
    if (iframe.contentWindow) {
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
  export interface IOptions extends MainAreaWidget.IOptionsOptionalContent {
    /**
     * The Voila URL.
     */
    url: string;

    /**
     * The preview label.
     */
    label: string;

    /**
     * The notebook document context.
     */
    context: DocumentRegistry.IContext<INotebookModel>;

    /**
     * Whether to reload the preview on context saved.
     */
    renderOnSave: boolean;
  }
}

/**
 * A namespace for module private data.
 */
namespace Private {
  /**
   * Counter used as a voila preview widget id.
   */
  export let count = 0;
}
