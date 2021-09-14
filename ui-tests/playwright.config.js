const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  ...baseConfig,
  timeout: 120000,
  reporter: [
    [process.env.CI ? 'dot' : 'list'],
    [
      '@jupyterlab/galata/lib/benchmarkReporter',
      { outputFile: 'voila-benchmark.json' }
    ],
    ['@playwright/test/lib/test/reporters/html']
  ],
  use: {
    baseURL: 'http://localhost:8866/voila/',
    video: 'retain-on-failure'
  },
  // Try one retry as some tests are flaky
  retries: 1
};
