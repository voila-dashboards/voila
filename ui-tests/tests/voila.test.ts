// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { expect, test } from '@playwright/test';

test.describe('Notebook Tests', () => {
  test('Create New Notebook', async ({ page }) => {
    // render the notebook
    await page.goto('render/tests/notebooks/basics.ipynb');

    // wait for the widgets to load
    // await page.waitForSelector('.jupyter-widgets');
    await page.waitForSelector('span[role="presentation"] >> text=x');

    // change the value of the slider
    await page.fill('text=4.00', '8.00');
    await page.keyboard.down('Enter');

    // fetch the value of the label
    const value = await page.$eval('input', el => el.value);
    expect(value).toBe('64');

    // wait for the final MathJax message to be hidden
    await page.$('text=Typesetting math: 100%');
    await page.waitForSelector('#MathJax_Message', { state: 'hidden' });

    expect(await page.screenshot()).toMatchSnapshot('basics.png');
  });
});
