const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  ...baseConfig,
  use: {
    appPath: '/voila',
    autoGoto: false
  },
  // Switch to 'always' to keep raw assets for all tests
  preserveOutput: 'failures-only', // Breaks HTML report if use.video == 'on'
  // Try one retry as some tests are flaky
  retries: 1
};
