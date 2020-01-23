import { IFrame, ToolbarButton, ReactWidget, MainAreaWidget } from "@jupyterlab/apputils";

import {
  DocumentRegistry
} from "@jupyterlab/docregistry";

import { INotebookModel } from "@jupyterlab/notebook";

import { Signal } from '@phosphor/signaling';

import * as React from "react";

export const VOILA_ICON_CLASS = "jp-MaterialIcon jp-VoilaIcon";

export class VoilaPreview extends MainAreaWidget<IFrame> {
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
      onClick: () => { this.reload(); }
    });

    const renderOnSaveCheckbox = ReactWidget.create(
      <label className="jp-VoilaPreview-renderOnSave">
        <input
          style={{ verticalAlign: "middle" }}
          name="renderOnSave"
          type="checkbox"
          defaultChecked={this.renderOnSave}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            this.renderOnSave = event.target.checked;
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

  dispose() {
    if (this.isDisposed) {
      return;
    }
    Signal.clearData(this);
  }

  reload() {
    const iframe = this.content.node.querySelector("iframe")!;
    if (iframe.contentWindow) {
      iframe.contentWindow.location.reload();
    }
  }

  get renderOnSave(): boolean {
    return this._renderOnSave;
  }

  set renderOnSave(renderOnSave: boolean) {
    this._renderOnSave = renderOnSave;
  }

  private _renderOnSave: boolean;
}

export namespace VoilaPreview {
  export interface IOptions extends MainAreaWidget.IOptionsOptionalContent {
    url: string;
    label: string;
    context: DocumentRegistry.IContext<INotebookModel>;
    renderOnSave: boolean;
  }
}

namespace Private {
  export let count = 0;
}