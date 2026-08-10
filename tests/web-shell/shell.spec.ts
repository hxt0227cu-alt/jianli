import { test, expect } from '@playwright/test';
test('desktop shell exposes resume workspace and project playback', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: '先看简历，再聊项目。' })).toBeVisible();
  await page.getByRole('button', { name: '项目说明' }).click();
  await expect(page.getByRole('heading', { name: '用播放式演示讲清楚项目。' })).toBeVisible();
  await page.getByRole('button', { name: '播放下一页' }).click();
  await expect(page.getByRole('heading', { name: 'Agent 边界' })).toBeVisible();
  await page.getByRole('button', { name: '项目 02 · sleep AIoT' }).click();
  await expect(page.getByRole('heading', { name: '系统全景' })).toBeVisible();
});
test('narrow viewport is explicitly blocked', async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 720 });
  await page.goto('/');
  await expect(page.getByText('请使用桌面端访问')).toBeVisible();
});
