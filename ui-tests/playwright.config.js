const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  ...baseConfig,
  timeout: 240000,
  reporter: [
    [process.env.CI ? 'dot' : 'list'],
    [
      '@jupyterlab/galata/lib/benchmarkReporter',
      { outputFile: 'voila-benchmark.json' }
    ],
    ['html']
  ],
  use: {
    baseURL: 'http://localhost:8866',
    video: 'retain-on-failure'
  },
  // Try one retry as some tests are flaky
  retries: 1,
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.05
    }
  },
  webServer: {
    command:
      process.env.PROGRESSIVE_RENDERING === 'true'
        ? 'voila ../notebooks --no-browser --show_tracebacks True --progressive_rendering=true'
        : 'voila ../notebooks --no-browser --show_tracebacks True',
    url: 'http://localhost:8866',
    timeout: 360000,
    reuseExistingServer: !process.env.CI
  }
};
