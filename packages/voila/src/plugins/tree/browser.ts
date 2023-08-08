import { FileBrowser, DirListing } from '@jupyterlab/filebrowser';
import { VoilaDirListing } from './listing';

export class VoilaFileBrowser extends FileBrowser {
  /**
   * Create the underlying DirListing instance.
   *
   * @param options - The DirListing constructor options.
   *
   * @returns The created DirListing instance.
   */
  protected createDirListing(options: DirListing.IOptions): DirListing {
    return new VoilaDirListing(options);
  }
}
