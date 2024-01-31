import { FileBrowser, DirListing } from '@jupyterlab/filebrowser';
import { VoilaDirListing } from './listing';
import { Widget } from '@lumino/widgets';

export class VoilaFileBrowser extends FileBrowser {
  constructor(options: VoilaFileBrowser.IOptions) {
    const { urlFactory, title, ...rest } = options;
    super(rest);
    (this.listing as VoilaDirListing).urlFactory = urlFactory;
    this.addClass('voila-FileBrowser');

    const titleWidget = new Widget();
    titleWidget.node.innerText = title;
    this.toolbar.addItem('title', titleWidget);
  }
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

export namespace VoilaFileBrowser {
  export interface IOptions extends FileBrowser.IOptions {
    urlFactory: (path: string) => string;
    title: string;
  }
}
