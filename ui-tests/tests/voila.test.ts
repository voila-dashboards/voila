// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { galata, describe, test } from '@jupyterlab/galata';

import * as path from 'path';

jest.setTimeout(100000);

describe('Voila Visual Regression', () => {
  beforeAll(async () => {
    await galata.resetUI();
    galata.context.capturePrefix = 'voila';
  });

  afterAll(async () => {
    galata.context.capturePrefix = '';
  });

  test('Upload files to JupyterLab', async () => {
    await galata.contents.moveDirectoryToServer(
      path.resolve(__dirname, './notebooks'),
      'uploaded'
    );
    expect(
      await galata.contents.fileExists('uploaded/basics.ipynb')
    ).toBeTruthy();
  });

  test('Refresh File Browser', async () => {
    await galata.filebrowser.refresh();
  });

  test('Open directory uploaded', async () => {
    await galata.filebrowser.openDirectory('uploaded');
    expect(
      await galata.filebrowser.isFileListedInBrowser('basics.ipynb')
    ).toBeTruthy();
  });

  test('Open basics.ipynb with the Voila preview', async () => {
    const notebook = 'basics.ipynb';
    await galata.notebook.open(notebook);
    expect(await galata.notebook.isOpen(notebook)).toBeTruthy();
    await galata.notebook.activate(notebook);
    expect(await galata.notebook.isActive(notebook)).toBeTruthy();

    const page = galata.context.page;
    const previewSelector = '.jp-ToolbarButton .voilaRender';
    const button = await page.$(previewSelector);
    button.click();

    await galata.notebook.close(true);
    await galata.toggleSimpleMode(true);

    const iframe = await page.waitForSelector('iframe');
    const contentFrame = await iframe.contentFrame();

    await contentFrame.waitForSelector('.jupyter-widgets');
    await contentFrame.waitForLoadState('networkidle');

    // wait for the final MathJax message to be hidden
    await contentFrame.$('text=Typesetting math: 100%');
    await contentFrame.waitForSelector('#MathJax_Message', { state: 'hidden' });

    const imageName = 'basics';
    await galata.capture.screenshot(imageName, iframe);
    expect(await galata.capture.compareScreenshot(imageName)).toBe('same');
  });

  test('Open home directory', async () => {
    await galata.filebrowser.openHomeDirectory();
  });

  test('Delete uploaded directory', async () => {
    await galata.contents.deleteDirectory('uploaded');
  });
});
