import { test, expect } from '@playwright/test';
test('desktop shell exposes home and project evidence', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto('/');
  await expect(page.locator('.intro h1')).toBeVisible();
  await page.locator('.primary').first().click();
  await expect(page.locator('.page-heading h1')).toBeVisible();
  await expect(page.getByText('Sleep AIoT Agent')).toBeVisible();
});
test('narrow viewport is explicitly blocked', async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 720 });
  await page.goto('/');
  await expect(page.locator('.desktop-gate')).toBeVisible();
});
