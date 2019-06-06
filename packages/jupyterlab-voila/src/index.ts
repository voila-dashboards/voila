import {
  JupyterLab, JupyterLabPlugin
} from '@jupyterlab/application';

import {
  INotebookTracker, NotebookPanel, INotebookModel
} from '@jupyterlab/notebook';

import { IDocumentManager } from '@jupyterlab/docmanager';

import {
  ReadonlyJSONObject
} from '@phosphor/coreutils';

import {
    ICommandPalette, MainAreaWidget, IFrame,
} from '@jupyterlab/apputils';

import {
  IMainMenu
} from '@jupyterlab/mainmenu';

import {
  PageConfig
} from '@jupyterlab/coreutils';	

import {
  ToolbarButton
} from '@jupyterlab/apputils';

import { DocumentRegistry } from "@jupyterlab/docregistry";

import { IDisposable } from '@phosphor/disposable';

import '../style/index.css';

class VoilaRenderButton implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {

  constructor(app: JupyterLab) {
    this.app = app;
  }

  readonly app: JupyterLab;

  createNew(panel: NotebookPanel, context: DocumentRegistry.IContext<INotebookModel>): IDisposable {
    let renderVoila = () => {
      this.app.commands.execute('notebook:render-with-voila');
    };

    let button = new ToolbarButton({
      className: 'voilaRender',
      iconClassName: 'fa fa-desktop',
      onClick: renderVoila,
      label: 'Voila',
      tooltip: 'Render with Voila'
    });

    panel.toolbar.insertItem(9, 'voilaRender', button);

    return button;
  }
}

/**
 * Initialization data for the jupyterlab-voila extension.
 */
const extension: JupyterLabPlugin<void> = {
  id: 'jupyterlab-voila',
  autoStart: true,
  requires: [INotebookTracker, ICommandPalette, IMainMenu, IDocumentManager],
  activate: (app: JupyterLab, notebooks: INotebookTracker, palette: ICommandPalette, menu: IMainMenu | null, docManager: IDocumentManager) => {

    function getCurrent(args: ReadonlyJSONObject): NotebookPanel | null {
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

    let counter = 0;

    function voilaIFrame(url: string, text: string): MainAreaWidget {
      let content = new IFrame();

      content.url = url;
      content.title.label = text;
      content.id = `voila-${++counter}`;
      let widget = new MainAreaWidget({ content });
      return widget;
    }

    app.commands.addCommand(CommandIDs.voilaRender, {
        label: 'Render Notebook with Voila',
        execute: async (args) => {
          const current = getCurrent(args);

          if (current) {
            const voilaPath = current.context.path;
            const baseUrl = PageConfig.getBaseUrl();
            const voilaUrl = baseUrl + "voila/render/" + voilaPath;

            let widget = voilaIFrame(voilaUrl, "Voila");
            app.shell.addToMainArea(widget, { mode: 'split-right'});
            return widget;
          }
        },
        isEnabled
    });

    palette.addItem({command:CommandIDs.voilaRender, category:'Notebook Operations'})

    let voilaButton = new VoilaRenderButton(app);
    app.docRegistry.addWidgetExtension('Notebook', voilaButton);

    menu.viewMenu.addGroup([
      {
        command: CommandIDs.voilaRender
      }
    ], 1000)
    
  }
};

export default extension;
export namespace CommandIDs{
    export const voilaRender = 'notebook:render-with-voila'
}
