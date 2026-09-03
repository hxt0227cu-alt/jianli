import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests/web-shell',
  testMatch: /.*\.spec\.ts/,
  forbidOnly: true,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'line',
  webServer: {
    command: 'pnpm preview --host 127.0.0.1 --port 5180',
    url: 'http://127.0.0.1:5180',
    reuseExistingServer: false,
  },
  use: {
    baseURL: 'http://127.0.0.1:5180',
    browserName: 'chromium',
  },
});
