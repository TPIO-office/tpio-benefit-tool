const { test, expect } = require('@playwright/test');

test.describe('Links', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/accounts/login/');
    await page.fill('[name="username"]', 'analyst');
    await page.fill('[name="password"]', 'analyst123');
    await page.click('button[type="submit"]');
  });

  test('should list links for assessment', async ({ page }) => {
    await page.goto('/assessments/1/links/');
    await expect(page).toHaveURL(/\/assessments\/1\/links\//);
  });

  test('should show link creation form', async ({ page }) => {
    await page.goto('/assessments/1/links/create/');
    await expect(page.locator('form')).toBeVisible({ timeout: 5000 });
  });
});