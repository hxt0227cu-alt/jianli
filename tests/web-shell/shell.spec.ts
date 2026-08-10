import { test, expect } from '@playwright/test';
test('desktop shell exposes home and project evidence', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: '先看证据，再聊实现。' })).toBeVisible();
  await page.getByRole('button', { name: '查看项目证据' }).click();
  await expect(page.getByRole('heading', { name: /两个项目/ })).toBeVisible();
  await expect(page.getByText('Sleep AIoT Agent')).toBeVisible();
});
test('narrow viewport is explicitly blocked', async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 720 });
  await page.goto('/');
  await expect(page.getByText('请使用桌面端访问')).toBeVisible();
});
