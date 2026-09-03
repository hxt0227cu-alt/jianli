import { test, expect } from '@playwright/test';

test('desktop shell exposes resume, sign-in, and three complete project stories', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: '先看简历，再聊项目。' })).toBeVisible();
  await expect(page.getByRole('img', { name: '简历预览' })).toBeVisible();

  await page.locator('.topbar').getByRole('button', { name: '预约面试' }).click();
  await expect(page.getByRole('heading', { name: '预约一次有准备的交流。' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '面试官登录' })).toBeVisible();

  await page.locator('.topbar').getByRole('button', { name: '项目说明' }).click();
  await expect(page.getByRole('main').getByRole('button', { name: '预约面试' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '让代表我发言的 Agent 有据可答、有权才做、失败可追踪。' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '别只看架构，直接挑战它。' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '结果、门禁和失败，都留证据。' })).toBeVisible();

  await page.getByRole('button', { name: '项目 02 · sleep AIoT' }).click();
  await expect(page.getByRole('heading', { name: '让会操作设备的 Agent 可控、可恢复、可评测。' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '不是“接了 Kafka”，而是把 51 条幽灵重复追到类型边界。' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '安全、性能和上云，按证据等级拆开说。' })).toBeVisible();

  await page.getByRole('button', { name: '项目 03 · litchi' }).click();
  await expect(page.getByRole('heading', { name: '在无 GPU、单人开发约束下，完成可控 Agent 与农技协同闭环。' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '一个人交付，不等于把所有责任都交给模型。' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '答辩分数之外，更值钱的是我知道数据能证明什么。' })).toBeVisible();
});

test('narrow viewport is explicitly blocked', async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 720 });
  await page.goto('/');
  await expect(page.getByText('请使用桌面端访问')).toBeVisible();
});

for (const width of [1024, 1100, 1200, 1280]) {
  test(`${width}px desktop navigation remains visible and clickable`, async ({ page }) => {
    await page.setViewportSize({ width, height: 720 });
    await page.goto('/');
    await expect(page.getByText('请使用桌面端访问')).toBeHidden();
    const topbar = page.locator('.topbar');
    const topbarBox = await topbar.boundingBox();
    expect(topbarBox).not.toBeNull();
    for (const label of ['简历问答', '项目说明', '预约面试', '我的预约']) {
      const button = topbar.getByRole('button', { name: label });
      await expect(button).toBeVisible();
      const box = await button.boundingBox();
      expect(box).not.toBeNull();
      expect(box!.x).toBeGreaterThanOrEqual(topbarBox!.x);
      expect(box!.x + box!.width).toBeLessThanOrEqual(topbarBox!.x + topbarBox!.width + 1);
      expect(box!.y).toBeGreaterThanOrEqual(topbarBox!.y);
      expect(box!.y + box!.height).toBeLessThanOrEqual(topbarBox!.y + topbarBox!.height + 1);
      await button.click();
    }
  });
}

test('anonymous booking page does not open protected slot streams', async ({ page }) => {
  const protectedRequests: string[] = [];
  page.on('request', (request) => {
    if (/\/slots\/(events|snapshot)/.test(request.url())) protectedRequests.push(request.url());
  });
  await page.goto('/');
  await page.locator('.topbar').getByRole('button', { name: '预约面试' }).click();
  await expect(page.getByRole('heading', { name: '面试官登录' })).toBeVisible();
  await page.waitForTimeout(500);
  expect(protectedRequests).toEqual([]);
});
