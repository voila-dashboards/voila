// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { expect, test } from '@playwright/test';

test.describe('Voila stability Tests', () => {
  let errorLogs: string;
  test.beforeEach(({ page }) => {
    page.setDefaultTimeout(120000);
    errorLogs = '';
    page.on('console', message => {
      if (message.type() === 'error') {
        errorLogs += message.text() + '\n';
      }
    });
  });
  test.afterEach(async ({ page, browserName }) => {
    await page.close({ runBeforeUnload: true });
  });
  test('Should render notebook with missing module', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'missing_module';
    await page.goto(`render/${notebookName}.ipynb`);
    await page.waitForSelector('button');
    await page.$('text=Typesetting math: 100%');
    await page.waitForSelector('#MathJax_Message', { state: 'hidden' });
    expect(errorLogs).toContain(
      'Class ModuleImportErrorModel not found in module widget_lib@^0.1.0'
    );
    expect(await page.screenshot()).toMatchSnapshot(`${notebookName}.png`);
  });

  test('Should render notebook with model error', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'module_error';
    await page.goto(`render/${notebookName}.ipynb`);
    await page.waitForSelector('button');
    await page.$('text=Typesetting math: 100%');
    await page.waitForSelector('#MathJax_Message', { state: 'hidden' });
    expect(errorLogs).toContain('Error: Failed to initialize model.');
    expect(await page.screenshot()).toMatchSnapshot(`${notebookName}.png`);
  });

  test('Should render notebook with render error', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'render_error';
    await page.goto(`render/${notebookName}.ipynb`);
    await page.waitForSelector('button');
    await page.$('text=Typesetting math: 100%');
    await page.waitForSelector('#MathJax_Message', { state: 'hidden' });
    expect(errorLogs).toContain('Error: Could not create view');
    expect(await page.screenshot()).toMatchSnapshot(`${notebookName}.png`);
  });
});
