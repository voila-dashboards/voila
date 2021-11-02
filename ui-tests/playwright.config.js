const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  projects: [
    {
      ...baseConfig,
      name: 'voila',
      timeout: 240000,
      use: {
        baseURL: 'http://localhost:8866/voila/',
        video: 'retain-on-failure'
      },
      // Try one retry as some tests are flaky
      retries: 1
    },
    {
      ...baseConfig,
      name: 'voila-fps',
      timeout: 240000,
      use: {
        baseURL: 'http://localhost:8867/voila/',
        video: 'retain-on-failure'
      },
      // Try one retry as some tests are flaky
      retries: 1
    }
  ],
  reporter: [
    [process.env.CI ? 'dot' : 'list'],
    [
      '@jupyterlab/galata/lib/benchmarkReporter',
      { outputFile: 'voila-benchmark.json' }
    ],
    ['html']
  ]
};
