// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { test } from '@jupyterlab/galata';

import { expect } from '@playwright/test';

test.describe('Notebook Tests', () => {
  test('Create New Notebook', async ({ page }) => {
    // render the notebook
    await page.goto('render/tests/notebooks/basics.ipynb');

    await page.waitForSelector('.jupyter-widgets');

    // wait for the final MathJax message to be hidden
    await page.$('text=Typesetting math: 100%');
    await page.waitForSelector('#MathJax_Message', { state: 'hidden' });

    // TODO: move slider and check value
    expect(true).toBe(true);
  });
});
