// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { expect, test } from '@playwright/test';
import { addBenchmarkToTest } from './utils';

const PREFIX =
  process.env.PROGRESSIVE_RENDERING === 'true' ? 'progressive_rendering_' : '';
test.describe('Voila performance Tests', () => {
  test.beforeEach(({ page }) => {
    page.setDefaultTimeout(120000);
  });
  test.afterEach(async ({ page, browserName }) => {
    await page.close({ runBeforeUnload: true });
  });
  test('Render tree classic', async ({ page, browserName }, testInfo) => {
    const testFunction = async () => {
      await page.goto('?classic-tree=true');
      // wait for page to load
      await page.waitForSelector('.list-header');
    };
    await addBenchmarkToTest(
      'voila-tree-classic',
      testFunction,
      testInfo,
      browserName
    );

    // await expect(page).toHaveScreenshot('voila-tree-classic.png');
    await expect(page).toHaveScreenshot(`${PREFIX}voila-tree-classic.png`);
  });

  test('Render tree light theme', async ({ page, browserName }, testInfo) => {
    const testFunction = async () => {
      await page.goto('');
      // wait for page to load
      await page.waitForSelector('.voila-FileBrowser');
    };
    await addBenchmarkToTest(
      'voila-tree-light',
      testFunction,
      testInfo,
      browserName
    );

    await expect(page).toHaveScreenshot(`${PREFIX}voila-tree-light.png`);
  });

  test('Render tree dark theme', async ({ page, browserName }, testInfo) => {
    const testFunction = async () => {
      await page.goto('?theme=dark');
      // wait for page to load
      await page.waitForSelector('.voila-FileBrowser');
    };
    await addBenchmarkToTest(
      'voila-tree-dark',
      testFunction,
      testInfo,
      browserName
    );

    await expect(page).toHaveScreenshot(`${PREFIX}voila-tree-dark.png`);
  });

  test('Render tree miami theme', async ({ page, browserName }, testInfo) => {
    const testFunction = async () => {
      await page.goto('?theme=JupyterLab%20Miami%20Nights');
      // wait for page to load
      await page.waitForSelector('.voila-FileBrowser');
    };
    await addBenchmarkToTest(
      'voila-tree-miami',
      testFunction,
      testInfo,
      browserName
    );

    await expect(page).toHaveScreenshot(`${PREFIX}voila-tree-miami.png`);
  });

  test('Render and benchmark basics.ipynb with classic template', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'basics';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb?template=classic`);
      // wait for the widgets to load
      await page.waitForSelector('.slider-container');
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);

    // wait for the final MathJax message to be hidden
    await page.$('text=Typesetting math: 100%');
    await page.waitForSelector('#MathJax_Message', { state: 'hidden' });
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}-classic.png`);
  });

  test('Render and benchmark basics.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'basics';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      // wait for the widgets to load
      await page.waitForSelector('.slider-container');
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    // change the value of the slider
    await page.fill('text=4.00', '8.00');
    await page.keyboard.down('Enter');
    await page.waitForTimeout(500);
    // fetch the value of the label
    const value = await page.$eval('input', (el) => el.value);

    expect(value).toBe('64');
    // wait for the final MathJax message to be hidden
    await page.$('text=Typesetting math: 100%');
    await page.waitForSelector('#MathJax_Message', { state: 'hidden' });
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });

  test('Render basics.ipynb with dark theme', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'basics';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb?theme=dark`);
      // wait for the widgets to load
      await page.waitForSelector('.slider-container');
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);

    // wait for the final MathJax message to be hidden
    await page.$('text=Typesetting math: 100%');
    await page.waitForSelector('#MathJax_Message', { state: 'hidden' });
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}-dark.png`);
  });

  test('Render basics.ipynb with miami theme', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'basics';
    const testFunction = async () => {
      await page.goto(
        `/voila/render/${notebookName}.ipynb?theme=JupyterLab%20Miami%20Nights`
      );
      // wait for the widgets to load
      await page.waitForSelector('.slider-container');
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);

    // wait for the final MathJax message to be hidden
    await page.$('text=Typesetting math: 100%');
    await page.waitForSelector('#MathJax_Message', { state: 'hidden' });
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}-miami.png`);
  });

  test('Render 404 error', async ({ page }) => {
    await page.goto('/voila/render/unknown.ipynb');
    await page.waitForSelector('.voila-error');

    await expect(page).toHaveScreenshot('404.png');
  });

  test('Render 404 error with classic template', async ({ page }) => {
    await page.goto('/voila/render/unknown.ipynb?template=classic');
    await page.waitForSelector('.voila-error');

    await expect(page).toHaveScreenshot('404-classic.png');
  });

  test('Render 404 error with dark theme', async ({ page }) => {
    await page.goto('/voila/render/unknown.ipynb?theme=dark');
    await page.waitForSelector('.voila-error');

    await expect(page).toHaveScreenshot('404-dark.png');
  });

  test('Render and benchmark bqplot.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'bqplot';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      await page.waitForSelector('svg.svg-figure');
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });

  test('Render and benchmark dashboard.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'dashboard';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      await page.waitForSelector('svg.svg-figure');
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    const title = await page.$$('text.mainheading');
    expect(title).toHaveLength(2);
    expect(await title[0].innerHTML()).toEqual('Histogram');
    expect(await title[1].innerHTML()).toEqual('Line Chart');
  });

  test('Render and benchmark gridspecLayout.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'gridspecLayout';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      await page.waitForSelector(
        'button.jupyter-widgets.jupyter-button.widget-button >> text=10'
      );
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });

  test('Render and benchmark interactive.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'interactive';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      await page.waitForSelector('div.widget-slider.widget-hslider');
      await page.fill('div.widget-readout', '8.00');
      await page.keyboard.down('Enter');
      await page.fill('div.widget-readout >> text=0', '8.00');
      await page.keyboard.down('Enter');
      await page.mouse.click(0, 0);
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });

  test('Render and benchmark ipympl.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'ipympl';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      await page.waitForSelector('div.jupyter-matplotlib-figure');
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });

  test('Render and benchmark mimerenderers.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'mimerenderers';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      await page.waitForSelector('.biojs_msa_div');
      await page.waitForSelector('#MathJax_Message', { state: 'hidden' });
      await page.waitForTimeout(2000);
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });

  test('Render and benchmark bokeh.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'bokeh';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      await page.waitForSelector('.bk-Canvas');
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });

  test('Benchmark the multiple widgets notebook', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'multiple_widgets';
    const testMultipleWidget = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      await page.waitForSelector(
        'button.jupyter-widgets.jupyter-button.widget-button >> text=400'
      );
    };
    await addBenchmarkToTest(
      notebookName,
      testMultipleWidget,
      testInfo,
      browserName
    );
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });

  test('Render and benchmark query-strings.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'query-strings';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      await page.waitForSelector(
        'div.lm-Widget[data-mime-type="application/vnd.jupyter.stdout"]'
      );
      const userName = await page.$$(
        'div.jp-RenderedText.jp-OutputArea-output > pre'
      );
      expect(await userName[1].innerHTML()).toContain('Hi Kim');
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    await page.goto(`/voila/render/${notebookName}.ipynb?username=Riley`);
    await page.waitForSelector(
      'div.lm-Widget[data-mime-type="application/vnd.jupyter.stdout"]'
    );
    const userName = await page.$$(
      'div.jp-RenderedText.jp-OutputArea-output > pre'
    );
    expect(await userName[1].innerHTML()).toContain('Hi Riley');
    await page.$('text=Typesetting math: 100%');
    await page.waitForSelector('#MathJax_Message', { state: 'hidden' });
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });

  test('Render and benchmark reveal.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'reveal';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
      await page.waitForSelector('.slider-container');
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });

  test('Render yaml.ipynb', async ({ page, browserName }, testInfo) => {
    const notebookName = 'yaml';
    await page.goto(`/voila/render/${notebookName}.ipynb`);
    await page.waitForSelector('span >> text=hey');
    await expect(page).toHaveScreenshot(`${PREFIX}${notebookName}.png`);
  });
});
