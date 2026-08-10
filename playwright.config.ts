import { defineConfig } from '@playwright/test';
export default defineConfig({ testDir: 'tests/web-shell', testMatch: /.*\.spec\.ts/, webServer: { command: 'pnpm dev --host 127.0.0.1 --port 5180', url: 'http://127.0.0.1:5180', reuseExistingServer: false }, use: { baseURL: 'http://127.0.0.1:5180' } });
