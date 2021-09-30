const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  projects: [
    {
      ...baseConfig,
      name: 'render-and-benchmark',
      testDir: 'tests',
      timeout: 240000,
      use: {
        baseURL: 'http://localhost:8866/voila/',
        video: 'retain-on-failure'
      },
      // Try one retry as some tests are flaky
      retries: 0,
      workers: 2
    },
    {
      ...baseConfig,
      name: 'stability-test',
      testDir: 'stability_test',
      timeout: 240000,
      use: {
        baseURL: 'http://localhost:8868/voila/',
        video: 'retain-on-failure'
      },
      // Try one retry as some tests are flaky
      retries: 0,
      workers: 2
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
