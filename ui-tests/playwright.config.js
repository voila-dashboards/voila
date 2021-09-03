const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  ...baseConfig,
  use: {
    baseURL: 'http://localhost:8888/voila/'
  },
  // Try one retry as some tests are flaky
  retries: 1
};
