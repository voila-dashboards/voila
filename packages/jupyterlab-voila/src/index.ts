import {
  JupyterLab, JupyterLabPlugin
} from '@jupyterlab/application';

import {
  INotebookTracker, NotebookPanel
} from '@jupyterlab/notebook';

import {
  ReadonlyJSONObject
} from '@phosphor/coreutils';

import {
    ICommandPalette,
} from '@jupyterlab/apputils';

import {
  IMainMenu
} from '@jupyterlab/mainmenu';

import {
  PageConfig
} from '@jupyterlab/coreutils';	

import '../style/index.css';


/**
 * Initialization data for the jupyterlab-voila extension.
 */
const extension: JupyterLabPlugin<void> = {
  id: 'jupyterlab-voila',
  autoStart: true,
  requires: [INotebookTracker, ICommandPalette, IMainMenu],
  activate: (app: JupyterLab, notebooks: INotebookTracker, palette: ICommandPalette, menu: IMainMenu | null) => {
    console.log('JupyterLab extension jupyterlab-voila is activated!!!!!!!!');

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

    app.commands.addCommand(CommandIDs.voilaRender, {
        label: 'Open/Render Notebook with Voila',
        execute: async (args) => {
          const current = getCurrent(args);

          if (current) {
            const notebookPath = current.context.path;
            const voilaPath = notebookPath.slice(0, notebookPath.length-6);  // without .ipynb
            const baseUrl = PageConfig.getBaseUrl();
            const voilaUrl = baseUrl + "voila/render/" + voilaPath;
            window.open(voilaUrl)
          }
        },
        isEnabled
    });
    palette.addItem({command:CommandIDs.voilaRender, category:'Notebook Operations'})


    // TODO: what would be a good place to add it to the menu?
    // menu.fileMenu.addGroup(
    //     [
    //       { command: CommandIDs.voilaRender },
    //     ],
    //     1000
    // );
    
  }
};

export default extension;
export namespace CommandIDs{
    export const voilaRender = 'notebook:render-with-voila'
}
