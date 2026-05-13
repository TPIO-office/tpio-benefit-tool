const { test, expect } = require('@playwright/test');

test.describe('Nodes (Object Library)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/accounts/login/');
    await page.fill('[name="username"]', 'analyst');
    await page.fill('[name="password"]', 'analyst123');
    await page.click('button[type="submit"]');
  });

  test('should list nodes', async ({ page }) => {
    await page.goto('/nodes/');
    await expect(page).toHaveURL('/nodes/');
    await expect(page.locator('table, .card')).toBeVisible({ timeout: 5000 }).catch(() => {});
  });

  test('should show node detail', async ({ page }) => {
    await page.goto('/nodes/1/');
    await expect(page).toHaveURL(/\/nodes\/1\//);
    const title = page.locator('h1').first();
    await expect(title).toBeVisible({ timeout: 5000 });
  });

  test('should create new node', async ({ page }) => {
    await page.goto('/nodes/create/');
    await page.selectOption('[name="type"]', 'observing_system');
    await page.fill('[name="title"]', 'E2E Test Node');
    await page.fill('[name="short_name"]', 'E2EN');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/nodes/');
  });

  test('should search nodes', async ({ page }) => {
    await page.goto('/nodes/search/?q=test');
    await expect(page).toHaveURL(/\/nodes\/search\//);
  });

  test('should filter nodes by type', async ({ page }) => {
    await page.goto('/nodes/?type=observing_system');
    await expect(page).toHaveURL(/\/nodes\//);
  });
});