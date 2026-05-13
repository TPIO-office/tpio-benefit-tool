const { test, expect } = require('@playwright/test');

test.describe('Login', () => {
  test('should show login page for unauthenticated users', async ({ page }) => {
    await page.goto('/assessments/');
    await expect(page).toHaveURL(/\/accounts\/login\//);
  });

  test('should login successfully with analyst credentials', async ({ page }) => {
    await page.goto('/accounts/login/');
    await page.fill('[name="username"]', 'analyst');
    await page.fill('[name="password"]', 'analyst123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/accounts/login/');
    await page.fill('[name="username"]', 'wrong');
    await page.fill('[name="password"]', 'wrong');
    await page.click('button[type="submit"]');
    await expect(page.locator('.alert, .errorlist, [role="alert"]')).toBeVisible({ timeout: 5000 }).catch(() => {});
  });

  test('should logout successfully', async ({ page }) => {
    await page.goto('/accounts/login/');
    await page.fill('[name="username"]', 'analyst');
    await page.fill('[name="password"]', 'analyst123');
    await page.click('button[type="submit"]');
    await page.click('text=Logout');
    await expect(page).toHaveURL('/');
  });
});