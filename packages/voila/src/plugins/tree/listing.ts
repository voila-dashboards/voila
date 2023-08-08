import { DirListing } from '@jupyterlab/filebrowser';
import { Contents } from '@jupyterlab/services';
import { showErrorMessage } from '@jupyterlab/apputils';
import { PageConfig, URLExt } from '@jupyterlab/coreutils';

export class VoilaDirListing extends DirListing {
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
      const baseUrl = PageConfig.getBaseUrl();
      const frontend = PageConfig.getOption('frontend');
      const query = PageConfig.getOption('query');
      const url = URLExt.join(baseUrl, frontend, 'render', path) + `?${query}`;
      window.open(url, '_blank');
    }
  }
}
