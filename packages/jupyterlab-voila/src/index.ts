import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILayoutRestorer
} from "@jupyterlab/application";

import {
  ICommandPalette,
  WidgetTracker,
  ToolbarButton,
  DOMUtils
} from "@jupyterlab/apputils";

import { PageConfig, PathExt, ISettingRegistry } from "@jupyterlab/coreutils";

import { DocumentRegistry } from "@jupyterlab/docregistry";

import { IMainMenu } from "@jupyterlab/mainmenu";

import {
  INotebookTracker,
  NotebookPanel,
  INotebookModel
} from "@jupyterlab/notebook";

import { CommandRegistry } from "@phosphor/commands";

import { ReadonlyJSONObject } from "@phosphor/coreutils";

import { IDisposable } from "@phosphor/disposable";

import {
  VOILA_ICON_CLASS,
  VoilaPreview,
  IVoilaPreviewTracker
} from "./preview";

import "../style/index.css";

/**
 * The command IDs used by the plugin.
 */
export namespace CommandIDs {
  export const voilaRender = "notebook:render-with-voila";

  export const voilaOpen = "notebook:open-with-voila";
}

/**
 * A notebook widget extension that adds a voila preview button to the toolbar.
 */
class VoilaRenderButton
  implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  /**
   * Instantiate a new VoilaRenderButton.
   * @param commands The command registry.
   */
  constructor(commands: CommandRegistry) {
    this._commands = commands;
  }

  /**
   * Create a new extension object.
   */
  createNew(panel: NotebookPanel): IDisposable {
    const button = new ToolbarButton({
      className: "voilaRender",
      tooltip: "Render with Voila",
      iconClassName: VOILA_ICON_CLASS,
      onClick: () => {
        this._commands.execute(CommandIDs.voilaRender);
      }
    });
    panel.toolbar.insertAfter("cellType", "voilaRender", button);
    return button;
  }

  private _commands: CommandRegistry;
}

/**
 * Initialization data for the jupyterlab-voila extension.
 */
const extension: JupyterFrontEndPlugin<IVoilaPreviewTracker> = {
  id: "@jupyter-voila/jupyterlab-preview:plugin",
  autoStart: true,
  requires: [INotebookTracker],
  optional: [ICommandPalette, ILayoutRestorer, IMainMenu, ISettingRegistry],
  provides: IVoilaPreviewTracker,
  activate: (
    app: JupyterFrontEnd,
    notebooks: INotebookTracker,
    palette: ICommandPalette | null,
    restorer: ILayoutRestorer | null,
    menu: IMainMenu | null,
    settingRegistry: ISettingRegistry | null
  ) => {
    // Create a widget tracker for Voila Previews.
    const tracker = new WidgetTracker<VoilaPreview>({
      namespace: "voila-preview"
    });

    if (restorer) {
      restorer.restore(tracker, {
        command: CommandIDs.voilaRender,
        args: widget => ({
          id: widget.id,
          url: widget.content.url,
          label: widget.content.title.label
        }),
        name: widget => widget.id
      });
    }

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

    const { commands, docRegistry } = app;

    commands.addCommand(CommandIDs.voilaRender, {
      label: "Render Notebook with Voila",
      execute: async args => {
        const id = (args["id"] as string) || DOMUtils.createDomID();
        let url = args["url"] as string;
        let label = args["label"] as string;

        const current = getCurrent(args);
        let context: DocumentRegistry.IContext<INotebookModel>;
        if (current) {
          context = current.context;
          await context.save();
          const voilaPath = context.path;
          url = getVoilaUrl(voilaPath);
          label = PathExt.basename(voilaPath);
        }
        const widget = new VoilaPreview({ context, label, renderOnSave, url });
        widget.id = id;
        app.shell.add(widget, "main", { mode: "split-right" });
        void tracker.add(widget);
        return widget;
      },
      isEnabled
    });

    commands.addCommand(CommandIDs.voilaOpen, {
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

    const voilaButton = new VoilaRenderButton(commands);
    docRegistry.addWidgetExtension("Notebook", voilaButton);

    return tracker;
  }
};

export default extension;
