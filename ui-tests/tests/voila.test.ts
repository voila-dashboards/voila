// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { test } from '@jupyterlab/galata';

import { expect } from '@playwright/test';

test.describe('Notebook Tests', () => {
  test('Create New Notebook', async ({ page, tmpPath }) => {
    const fileName = 'create_test.ipynb';
    await page.notebook.createNew(fileName);
    expect(
      await page.waitForSelector(`[role="main"] >> text=${fileName}`)
    ).toBeTruthy();

    expect(await page.contents.fileExists(`${tmpPath}/${fileName}`)).toEqual(
      true
    );

    // await contentFrame.waitForSelector('.jupyter-widgets');
    // await contentFrame.waitForLoadState('networkidle');

    // // wait for the final MathJax message to be hidden
    // await contentFrame.$('text=Typesetting math: 100%');
    // await contentFrame.waitForSelector('#MathJax_Message', { state: 'hidden' });
  });
});
