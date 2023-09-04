import { DirListing } from '@jupyterlab/filebrowser';
import { Contents } from '@jupyterlab/services';
import { showErrorMessage } from '@jupyterlab/apputils';

export class VoilaDirListing extends DirListing {
  get urlFactory(): VoilaDirListing.IUrlFactory | undefined {
    return this._urlFactory;
  }
  set urlFactory(f: VoilaDirListing.IUrlFactory | undefined) {
    this._urlFactory = f;
  }

  /**
   * Handle the opening of an item.
   */
  protected handleOpen(item: Contents.IModel): void {
    if (item.type === 'directory') {
      const localPath = this.model.manager.services.contents.localPath(
        item.path
      );
      this.model
        .cd(`/${localPath}`)
        .catch((error) => showErrorMessage('Open directory', error));
    } else {
      const path = item.path;
      if (this.urlFactory) {
        window.open(this.urlFactory(path), '_blank');
      } else {
        showErrorMessage('Open file', 'URL Factory is not defined');
      }
    }
  }

  handleEvent(event: Event): void {
    if (event.type === 'click') {
      this.evtDblClick(event as MouseEvent);
    }
  }
  private _urlFactory: VoilaDirListing.IUrlFactory | undefined;
}

export namespace VoilaDirListing {
  export type IUrlFactory = (path: string) => string;
}
