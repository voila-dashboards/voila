import { MainAreaWidget, IFrame, ToolbarButton } from "@jupyterlab/apputils";

export const VOILA_ICON_CLASS = "jp-MaterialIcon jp-VoilaIcon";

export namespace VoilaPreview {
  export interface IOptions extends MainAreaWidget.IOptionsOptionalContent {
    url: string;
    label: string;
  }
}

export class VoilaPreview extends MainAreaWidget<IFrame> {
  constructor(options: VoilaPreview.IOptions) {
    let { url, label, ...opts } = options;
    super({
      ...opts,
      content: new IFrame({ sandbox: ["allow-same-origin", "allow-scripts"] })
    });

    this.content.url = url;
    this.content.title.label = label;
    this.content.title.icon = VOILA_ICON_CLASS;
    this.content.id = `voila-${++Private.count}`;

    const reloadButton = new ToolbarButton({
      // TODO: remove extras jp-Icon after migrating to JupyterLab 1.0
      iconClassName: "jp-RefreshIcon jp-Icon jp-Icon-16",
      onClick: () => {
        const iframe = this.content.node.querySelector("iframe")!;
        if (iframe.contentWindow) {
          iframe.contentWindow.location.reload();
        }
      },
      tooltip: "Reload Preview"
    });

    this.toolbar.addItem("reload", reloadButton);
  }
}

namespace Private {
  export let count = 0;
}
