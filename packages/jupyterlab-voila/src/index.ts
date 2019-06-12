import { JupyterLab, JupyterLabPlugin } from "@jupyterlab/application";

import {
  INotebookTracker,
  NotebookPanel,
  INotebookModel
} from "@jupyterlab/notebook";

import { ReadonlyJSONObject } from "@phosphor/coreutils";

import { ICommandPalette, MainAreaWidget, IFrame } from "@jupyterlab/apputils";

import { IMainMenu } from "@jupyterlab/mainmenu";

import { PageConfig, PathExt } from "@jupyterlab/coreutils";

import { ToolbarButton } from "@jupyterlab/apputils";

import { DocumentRegistry } from "@jupyterlab/docregistry";

import { IDisposable } from "@phosphor/disposable";

import "../style/index.css";

export namespace CommandIDs {
  export const voilaRender = "notebook:render-with-voila";

  export const voilaOpen = "notebook:open-with-voila";
}

const VOILA_ICON_CLASS = "jp-MaterialIcon jp-VoilaIcon";

class VoilaRenderButton
  implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  constructor(app: JupyterLab) {
    this.app = app;
  }

  readonly app: JupyterLab;

  createNew(
    panel: NotebookPanel,
    context: DocumentRegistry.IContext<INotebookModel>
  ): IDisposable {
    let renderVoila = () => {
      this.app.commands.execute("notebook:render-with-voila");
    };

    let button = new ToolbarButton({
      className: "voilaRender",
      iconClassName: VOILA_ICON_CLASS,
      onClick: renderVoila,
      tooltip: "Render with Voila"
    });

    panel.toolbar.insertItem(9, "voilaRender", button);

    return button;
  }
}

/**
 * Initialization data for the jupyterlab-voila extension.
 */
const extension: JupyterLabPlugin<void> = {
  id: "jupyterlab-voila",
  autoStart: true,
  requires: [INotebookTracker],
  optional: [ICommandPalette, IMainMenu],
  activate: (
    app: JupyterLab,
    notebooks: INotebookTracker,
    palette: ICommandPalette,
    menu: IMainMenu | null
  ) => {
    function getCurrent(args: ReadonlyJSONObject): NotebookPanel | null {
      const widget = notebooks.currentWidget;
      const activate = args["activate"] !== false;

      if (activate && widget) {
        app.shell.activateById(widget.id);
      }

      return widget;
    }

    function isEnabled(): boolean {
      return (
        notebooks.currentWidget !== null &&
        notebooks.currentWidget === app.shell.currentWidget
      );
    }

    let counter = 0;

    function voilaIFrame(url: string, text: string): MainAreaWidget {
      let content = new IFrame();

      content.url = url;
      content.title.label = text;
      content.title.icon = VOILA_ICON_CLASS;
      content.id = `voila-${++counter}`;
      let widget = new MainAreaWidget({ content });
      return widget;
    }

    function getVoilaUrl(path: string): string {
      const baseUrl = PageConfig.getBaseUrl();
      return `${baseUrl}voila/render/${path}`;
    }

    app.commands.addCommand(CommandIDs.voilaRender, {
      label: "Render Notebook with Voila",
      execute: async args => {
        const current = getCurrent(args);
        if (!current) {
          return;
        }
        const voilaPath = current.context.path;
        const voilaUrl = getVoilaUrl(voilaPath);
        const name = PathExt.basename(voilaPath);
        let widget = voilaIFrame(voilaUrl, name);
        app.shell.addToMainArea(widget, { mode: "split-right" });
        return widget;
      },
      isEnabled
    });

    app.commands.addCommand(CommandIDs.voilaOpen, {
      label: "Open with Voila in New Browser Tab",
      execute: async args => {
        const current = getCurrent(args);
        if (!current) {
          return;
        }
        const voilaUrl = getVoilaUrl(current.context.path);
        window.open(voilaUrl);
      },
      isEnabled
    });

    if (palette) {
      const category = "Notebook Operations";
      [CommandIDs.voilaRender, CommandIDs.voilaOpen].forEach(command => {
        palette.addItem({ command, category });
      });
    }

    if (menu) {
      menu.viewMenu.addGroup(
        [
          {
            command: CommandIDs.voilaRender
          },
          {
            command: CommandIDs.voilaOpen
          }
        ],
        1000
      );
    }

    let voilaButton = new VoilaRenderButton(app);
    app.docRegistry.addWidgetExtension("Notebook", voilaButton);
  }
};

export default extension;
