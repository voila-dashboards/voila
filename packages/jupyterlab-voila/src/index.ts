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

import { CommandRegistry } from "@phosphor/commands";

import { IDisposable } from "@phosphor/disposable";

import { VOILA_ICON_CLASS, VoilaPreview } from "./preview";

import "../style/index.css";

export namespace CommandIDs {
  export const voilaRender = "notebook:render-with-voila";

  export const voilaOpen = "notebook:open-with-voila";
}

class VoilaRenderButton
  implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  constructor(commands: CommandRegistry) {
    this._commands = commands;
  }

  createNew(panel: NotebookPanel): IDisposable {
    const renderVoila = () => {
      this._commands.execute("notebook:render-with-voila");
    };
    const button = new ToolbarButton({
      className: "voilaRender",
      iconClassName: VOILA_ICON_CLASS,
      onClick: renderVoila,
      tooltip: "Render with Voila"
    });

    panel.toolbar.insertAfter("cellType", "voilaRender", button);
    return button;
  }

  private _commands: CommandRegistry;
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
    settingRegistry: ISettingRegistry | null
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

    if (settingRegistry) {
      Promise.all([settingRegistry.load(extension.id), app.restored])
        .then(([settings]) => {
          updateSettings(settings);
          settings.changed.connect(updateSettings);
        })
        .catch((reason: Error) => {
          console.error(reason.message);
        });
    }

    app.commands.addCommand(CommandIDs.voilaRender, {
      label: "Render Notebook with Voila",
      execute: async args => {
        const current = getCurrent(args);
        if (!current) {
          return;
        }
        const { context } = current;
        await context.save();

        const voilaPath = context.path;
        const url = getVoilaUrl(voilaPath);
        const label = PathExt.basename(voilaPath);
        const widget = new VoilaPreview({ context, label, url, renderOnSave });
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

    const voilaButton = new VoilaRenderButton(app.commands);
    app.docRegistry.addWidgetExtension("Notebook", voilaButton);
  }
};

export default extension;
