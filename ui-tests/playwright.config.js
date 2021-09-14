const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  ...baseConfig,
  reporter: [
    [process.env.CI ? 'dot' : 'list'],
    [
      '@jupyterlab/galata/lib/benchmarkReporter',
      { outputFile: 'voila-benchmark.json' }
    ],
    ['@playwright/test/lib/test/reporters/html']
  ],
  use: {
    baseURL: 'http://localhost:8866/voila/'
  },
  // Try one retry as some tests are flaky
  retries: 0
};
