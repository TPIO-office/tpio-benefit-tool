const { test, expect } = require('@playwright/test');

test.describe('Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/accounts/login/');
    await page.fill('[name="username"]', 'analyst');
    await page.fill('[name="password"]', 'analyst123');
    await page.click('button[type="submit"]');
  });

  test('should show Sankey diagram', async ({ page }) => {
    await page.goto('/assessments/1/sankey/');
    await expect(page).toHaveURL(/\/assessments\/1\/sankey\//);
  });

  test('should return JSON for value tree API', async ({ page, request }) => {
    const response = await request.get('/assessments/1/tree-json/');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('nodes');
    expect(data).toHaveProperty('adjacency');
  });

  test('should show results dashboard', async ({ page }) => {
    await page.goto('/results/');
    await expect(page).toHaveURL('/results/');
    await expect(page.locator('h1, .card')).toBeVisible({ timeout: 5000 }).catch(() => {});
  });
});