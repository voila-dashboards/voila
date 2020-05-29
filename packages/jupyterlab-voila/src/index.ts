import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILayoutRestorer
} from "@jupyterlab/application";

import {
  ICommandPalette,
  WidgetTracker,
  ToolbarButton
} from "@jupyterlab/apputils";

import { ISettingRegistry } from "@jupyterlab/settingregistry";

import { PageConfig } from "@jupyterlab/coreutils";

import { DocumentRegistry } from "@jupyterlab/docregistry";

import { IMainMenu } from "@jupyterlab/mainmenu";

import {
  INotebookTracker,
  NotebookPanel,
  INotebookModel
} from "@jupyterlab/notebook";

import { IRunningSessionManagers, IRunningSessions } from "@jupyterlab/running";

import { KernelAPI, KernelManager, ServerConnection } from "@jupyterlab/services";

import { notebookIcon } from "@jupyterlab/ui-components";

import { toArray } from "@lumino/algorithm";

import { CommandRegistry } from "@lumino/commands";

import { ReadonlyJSONObject } from "@lumino/coreutils";

import { IDisposable } from "@lumino/disposable";

import {
  VOILA_ICON_CLASS,
  VoilaPreview,
  IVoilaPreviewTracker,
  VoilaPreviewFactory
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
      iconClass: VOILA_ICON_CLASS,
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
 * Initialization data for the jupyterlab-voila preview plugin.
 */
const preview: JupyterFrontEndPlugin<IVoilaPreviewTracker> = {
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
        command: "docmanager:open",
        args: panel => ({
          path: panel.context.path,
          factory: factory.name
        }),
        name: panel => panel.context.path,
        when: app.serviceManager.ready
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

    const factory = new VoilaPreviewFactory(getVoilaUrl, {
      name: "Voila-preview",
      fileTypes: ["notebook"],
      modelName: "notebook"
    });

    factory.widgetCreated.connect((sender, widget) => {
      // Notify the widget tracker if restore data needs to update.
      widget.context.pathChanged.connect(() => {
        void tracker.save(widget);
      });
      // Add the notebook panel to the tracker.
      void tracker.add(widget);
    });

    const updateSettings = (settings: ISettingRegistry.ISettings): void => {
      factory.defaultRenderOnSave = settings.get("renderOnSave")
        .composite as boolean;
    };

    if (settingRegistry) {
      Promise.all([settingRegistry.load(preview.id), app.restored])
        .then(([settings]) => {
          updateSettings(settings);
          settings.changed.connect(updateSettings);
        })
        .catch((reason: Error) => {
          console.error(reason.message);
        });
    }

    app.docRegistry.addWidgetFactory(factory);

    const { commands, docRegistry } = app;

    commands.addCommand(CommandIDs.voilaRender, {
      label: "Render Notebook with Voila",
      execute: async args => {
        const current = getCurrent(args);
        let context: DocumentRegistry.IContext<INotebookModel>;
        if (current) {
          context = current.context;
          await context.save();

          commands.execute("docmanager:open", {
            path: context.path,
            factory: "Voila-preview",
            options: {
              mode: "split-right"
            }
          });
        }
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

/**
 * A plugin to show the list of running Voila kernels.
 */
const kernels: JupyterFrontEndPlugin<void> = {
  id: "@jupyter-voila/jupyterlab-preview:kernels",
  autoStart: true,
  requires: [IRunningSessionManagers],
  activate: (app: JupyterFrontEnd, managers: IRunningSessionManagers) => {
    const serverSettings = ServerConnection.makeSettings({ baseUrl: "/voila" });
    const kernelManager = new KernelManager({ serverSettings });

    managers.add({
      name: "Voila",
      running: () => {
        return toArray(kernelManager.running())
          .map(model => new RunningKernel(model));
      },
      shutdownAll: () => kernelManager.shutdownAll(),
      refreshRunning: () => kernelManager.refreshRunning(),
      runningChanged: kernelManager.runningChanged
    });

    class RunningKernel implements IRunningSessions.IRunningItem {
      constructor(model: KernelAPI.IModel) {
        this._model = model;
      }
      open() {
        // no-op
      }
      shutdown() {
        return kernelManager.shutdown(this._model.id);
      }
      icon() {
        return notebookIcon;
      }
      label() {
        return this._model.id;
      }
      labelTitle() {
        return `name: ${this._model.name}`;
      }

      private _model: KernelAPI.IModel;
    }
  }
};

export default [preview, kernels];
