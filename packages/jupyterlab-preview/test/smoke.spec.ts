import { firefox, Browser, BrowserContext } from 'playwright';

describe('Smoke', () => {
  let browser: Browser;
  let context: BrowserContext;

  beforeAll(async () => {
    jest.setTimeout(200000);
    browser = await firefox.launch({ slowMo: 1000 });
    context = await browser.newContext({
      recordVideo: { dir: 'artifacts/videos/' }
    });
  });

  afterAll(async () => {
    await context.close();
    await browser.close();
  });

  describe('Open the preview', () => {
    it('should open the Voila preview', async () => {
      // Open new page
      const page = await context.newPage();

      await page.goto('http://localhost:8889/lab/workspaces/lab?reset');

      // Create a new Python notebook
      await Promise.all([
        page.waitForNavigation(),
        page.click(
          "//div[normalize-space(.)='Python 3' and normalize-space(@title)='Python 3']/div[1]"
        )
      ]);

      // Enter code in the first cell
      await page.click('pre[role="presentation"]');
      await page.fill('//textarea', 'from ipywidgets import IntSlider');
      await page.press('//textarea', 'Enter');
      await page.press('//textarea', 'Enter');
      await page.fill('//textarea', 'slider = IntSlider()');
      await page.press('//textarea', 'Enter');
      await page.fill('//textarea', 'slider');

      // Run the cell
      await page.click(
        "//button[normalize-space(@title)='Run the selected cells and advance']"
      );

      // Move the slider
      await page.click(
        "//div[2]/div/div[2]/div[normalize-space(.)='0']/div[1]"
      );

      // Open the Voila preview
      await page.click("//button[normalize-space(@title)='Render with Voilà']");

      // Wait a little bit
      await page.waitForTimeout(3000);

      // Reload the preview
      await page.click("//button[normalize-space(@title)='Reload Preview']");

      // Wait a little bit
      await page.waitForTimeout(3000);

      // Close page
      await page.close();

      // ---------------------
      await context.close();
      await browser.close();

      expect(true).toBe(true);
    });
  });
});
