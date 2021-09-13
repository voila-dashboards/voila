// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { expect, test } from '@playwright/test';
import { addBenchmarkToTest } from './utils';

test.describe('Voila performance Tests', () => {
  test('Render and benchmark basics.ipynb', async ({ page }, testInfo) => {
    const notebookName = 'basics';
    const testFunction = async () => {
      await page.goto(`render/${notebookName}.ipynb`);
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
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, 1);
    expect(await page.screenshot()).toMatchSnapshot(`${notebookName}.png`);
  });

  test('Render and benchmark bqplot.ipynb', async ({ page }, testInfo) => {
    const notebookName = 'bqplot';
    const testFunction = async () => {
      await page.goto(`render/${notebookName}.ipynb`);
      await page.waitForSelector('span[role="presentation"] >> text=x');
      await page.fill('text=4.00', '8.00');
      await page.keyboard.down('Enter');
      const value = await page.$eval('input', el => el.value);
      expect(value).toBe('64');
      await page.$('text=Typesetting math: 100%');
      await page.waitForSelector('#MathJax_Message', { state: 'hidden' });
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, 1);
    expect(await page.screenshot()).toMatchSnapshot(`${notebookName}.png`);
  });

  test('Benchmark the multiple widgets notebook', async ({
    page
  }, testInfo) => {
    const notebookName = 'multiple_widgets';
    const testMultipleWidget = async () => {
      await page.goto(`render/${notebookName}.ipynb`);
      await page.waitForSelector(
        'button.jupyter-widgets.jupyter-button.widget-button >> text=400'
      );
    };
    await addBenchmarkToTest(notebookName, testMultipleWidget, testInfo, 5);
    expect(await page.screenshot()).toMatchSnapshot(`${notebookName}.png`);
  });
});
