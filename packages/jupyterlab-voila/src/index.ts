import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from "@jupyterlab/application";

import {
  INotebookTracker,
  NotebookPanel,
  INotebookModel
} from "@jupyterlab/notebook";

import { ReadonlyJSONObject } from "@phosphor/coreutils";

import { ICommandPalette } from "@jupyterlab/apputils";

import { IMainMenu } from "@jupyterlab/mainmenu";

import { PageConfig, PathExt, ISettingRegistry } from "@jupyterlab/coreutils";

import { ToolbarButton } from "@jupyterlab/apputils";

import { DocumentRegistry } from "@jupyterlab/docregistry";

import { IDisposable } from "@phosphor/disposable";

import { VOILA_ICON_CLASS, VoilaPreview } from "./preview";

import "../style/index.css";

export namespace CommandIDs {
  export const voilaRender = "notebook:render-with-voila";

  export const voilaOpen = "notebook:open-with-voila";
}

class VoilaRenderButton
  implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  constructor(app: JupyterFrontEnd) {
    this.app = app;
  }

  readonly app: JupyterFrontEnd;

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

    panel.toolbar.insertAfter("cellType", "voilaRender", button);

    return button;
  }
}

/**
 * Initialization data for the jupyterlab-voila extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: "@jupyter-voila/jupyterlab-preview:plugin",
  autoStart: true,
  requires: [INotebookTracker],
  optional: [ICommandPalette, IMainMenu, ISettingRegistry],
  activate: (
    app: JupyterFrontEnd,
    notebooks: INotebookTracker,
    palette: ICommandPalette,
    menu: IMainMenu | null,
    settingRegistry: ISettingRegistry
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

    function getVoilaUrl(path: string): string {
      const baseUrl = PageConfig.getBaseUrl();
      return `${baseUrl}voila/render/${path}`;
    }

    let renderOnSave = false;

    const updateSettings = (settings: ISettingRegistry.ISettings): void => {
      renderOnSave = settings.get("renderOnSave").composite as boolean;
    };

    Promise.all([settingRegistry.load(extension.id), app.restored])
      .then(([settings]) => {
        updateSettings(settings);
        settings.changed.connect(updateSettings);
      })
      .catch((reason: Error) => {
        console.error(reason.message);
      });

    app.commands.addCommand(CommandIDs.voilaRender, {
      label: "Render Notebook with Voila",
      execute: async args => {
        const current = getCurrent(args);
        if (!current) {
          return;
        }
        await current.context.save();
        const voilaPath = current.context.path;
        const url = getVoilaUrl(voilaPath);
        const name = PathExt.basename(voilaPath);
        let widget = new VoilaPreview({
          url,
          label: name,
          context: current.context,
          renderOnSave
        });

        app.shell.add(widget, "main", { mode: "split-right" });
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
        await current.context.save();
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
