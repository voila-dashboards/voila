import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILayoutRestorer
} from '@jupyterlab/application';

import {
  ICommandPalette,
  WidgetTracker,
  ToolbarButton
} from '@jupyterlab/apputils';

import { ISettingRegistry } from '@jupyterlab/settingregistry';

import { PageConfig } from '@jupyterlab/coreutils';

import { DocumentRegistry } from '@jupyterlab/docregistry';

import { IMainMenu } from '@jupyterlab/mainmenu';

import {
  INotebookTracker,
  NotebookPanel,
  INotebookModel
} from '@jupyterlab/notebook';

import { CommandRegistry } from '@lumino/commands';

import { ReadonlyPartialJSONObject } from '@lumino/coreutils';

import { IDisposable } from '@lumino/disposable';

import {
  VoilaPreview,
  IVoilaPreviewTracker,
  VoilaPreviewFactory
} from './preview';

import { voilaIcon } from './icons';

/**
 * The command IDs used by the plugin.
 */
export namespace CommandIDs {
  export const voilaRender = 'notebook:render-with-voila';

  export const voilaOpen = 'notebook:open-with-voila';
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
      className: 'voilaRender',
      tooltip: 'Render with Voilà',
      icon: voilaIcon,
      onClick: () => {
        this._commands.execute(CommandIDs.voilaRender);
      }
    });
    panel.toolbar.insertAfter('cellType', 'voilaRender', button);
    return button;
  }

  private _commands: CommandRegistry;
}

/**
 * Initialization data for the jupyterlab-preview extension.
 */
const extension: JupyterFrontEndPlugin<IVoilaPreviewTracker> = {
  id: '@voila-dashboards/jupyterlab-preview:plugin',
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
    // Create a widget tracker for Voilà Previews.
    const tracker = new WidgetTracker<VoilaPreview>({
      namespace: 'voila-preview'
    });

    if (restorer) {
      restorer.restore(tracker, {
        command: 'docmanager:open',
        args: panel => ({
          path: panel.context.path,
          factory: factory.name
        }),
        name: panel => panel.context.path,
        when: app.serviceManager.ready
      });
    }

    function getCurrent(args: ReadonlyPartialJSONObject): NotebookPanel | null {
      const widget = notebooks.currentWidget;
      const activate = args['activate'] !== false;

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
      name: 'Voila-preview',
      fileTypes: ['notebook'],
      modelName: 'notebook'
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
      factory.defaultRenderOnSave = settings.get('renderOnSave')
        .composite as boolean;
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

    app.docRegistry.addWidgetFactory(factory);

    const { commands, docRegistry } = app;

    commands.addCommand(CommandIDs.voilaRender, {
      label: 'Render Notebook with Voilà',
      execute: async args => {
        const current = getCurrent(args);
        let context: DocumentRegistry.IContext<INotebookModel>;
        if (current) {
          context = current.context;
          await context.save();

          commands.execute('docmanager:open', {
            path: context.path,
            factory: 'Voila-preview',
            options: {
              mode: 'split-right'
            }
          });
        }
      },
      isEnabled
    });

    commands.addCommand(CommandIDs.voilaOpen, {
      label: 'Open with Voilà in New Browser Tab',
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
      const category = 'Notebook Operations';
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
    docRegistry.addWidgetExtension('Notebook', voilaButton);

    return tracker;
  }
};

export default extension;
