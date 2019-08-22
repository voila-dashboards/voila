import { MainAreaWidget, IFrame, ToolbarButton } from "@jupyterlab/apputils";
import { DocumentRegistry } from "@jupyterlab/docregistry";
import { INotebookModel } from "@jupyterlab/notebook";

export const VOILA_ICON_CLASS = "jp-MaterialIcon jp-VoilaIcon";

export namespace VoilaPreview {
  export interface IOptions extends MainAreaWidget.IOptionsOptionalContent {
    url: string;
    label: string;
    context: DocumentRegistry.IContext<INotebookModel>;
  }
}

export class VoilaPreview extends MainAreaWidget<IFrame> {
  constructor(options: VoilaPreview.IOptions) {
    super({
      ...options,
      content: new IFrame({ sandbox: ["allow-same-origin", "allow-scripts"] })
    });

    let { url, label, context } = options;

    this.content.url = url;
    this.content.title.label = label;
    this.content.title.icon = VOILA_ICON_CLASS;
    this.content.id = `voila-${++Private.count}`;

    const reloadButton = new ToolbarButton({
      iconClassName: "jp-RefreshIcon",
      onClick: this.reload,
      tooltip: "Reload Preview"
    });

    this._context = context;
    this._context.ready.then(() => {
      if (this.isDisposed) {
        return;
      }
      this._context.fileChanged.connect(this.onFileChanged, this);
    });

    this.toolbar.addItem("reload", reloadButton);
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
