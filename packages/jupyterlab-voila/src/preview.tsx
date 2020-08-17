import {
  MainAreaWidget,
  IFrame,
  ToolbarButton,
  ReactWidget
} from "@jupyterlab/apputils";
import { DocumentRegistry } from "@jupyterlab/docregistry";
import { INotebookModel } from "@jupyterlab/notebook";

import * as React from "react";

export const VOILA_ICON_CLASS = "jp-MaterialIcon jp-VoilaIcon";

export namespace VoilaPreview {
  export interface IOptions extends MainAreaWidget.IOptionsOptionalContent {
    url: string;
    label: string;
    context: DocumentRegistry.IContext<INotebookModel>;
    renderOnSave: boolean;
  }
}

export class VoilaPreview extends MainAreaWidget<IFrame> {
  constructor(options: VoilaPreview.IOptions) {
    super({
      ...options,
      content: new IFrame({ sandbox: ["allow-same-origin", "allow-scripts"] })
    });

    window.onmessage = (event: any) => {
      //console.log("EVENT: ", event);

      switch (event.data?.level) {
        case "debug":
          console.debug(...event.data?.msg);
          break;

        case "info":
          console.info(...event.data?.msg);
          break;

        case "warn":
          console.warn(...event.data?.msg);
          break;

        case "error":
          console.error(...event.data?.msg);
          break;

        default:
          console.log(event);
          break;
      }
    };

    let { url, label, context, renderOnSave } = options;

    this.content.url = url;
    this.content.title.label = label;
    this.content.title.icon = VOILA_ICON_CLASS;
    this.content.id = `voila-${++Private.count}`;

    const reloadButton = new ToolbarButton({
      iconClassName: "jp-RefreshIcon",
      onClick: this.reload,
      tooltip: "Reload Preview"
    });

    const renderOnSaveCheckbox = ReactWidget.create(
      <label>
        <input
          style={{ verticalAlign: "middle" }}
          name="renderOnSave"
          type="checkbox"
          defaultChecked={renderOnSave}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            this.renderOnSave = event.target.checked;
          }}
        />
        Render on Save
      </label>
    );
    renderOnSaveCheckbox.addClass("jp-VoilaPreview-renderOnSave");

    this.toolbar.addItem("reload", reloadButton);
    this.toolbar.addItem("renderOnSave", renderOnSaveCheckbox);

    this.renderOnSave = renderOnSave;

    this._context = context;
    this._context.ready.then(() => {
      if (this.isDisposed) {
        return;
      }
      this._context.fileChanged.connect(this.onFileChanged, this);
    });
  }

  dispose() {
    this._context.fileChanged.disconnect(this.onFileChanged, this);
    super.dispose();
  }

  reload = () => {
    const iframe = this.content.node.querySelector("iframe")!;
    if (iframe.contentWindow) {
      iframe.contentWindow.location.reload();
    }
  };

  get renderOnSave(): boolean {
    return this._renderOnSave;
  }

  set renderOnSave(renderOnSave: boolean) {
    this._renderOnSave = renderOnSave;
  }

  private onFileChanged(): void {
    if (!this.renderOnSave) {
      return;
    }
    this.reload();
  }

  private _context: DocumentRegistry.IContext<INotebookModel>;
  private _renderOnSave: boolean;
}

namespace Private {
  export let count = 0;
}
