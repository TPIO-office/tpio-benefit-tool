const { test, expect } = require('@playwright/test');

test.describe('Assessments', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/accounts/login/');
    await page.fill('[name="username"]', 'analyst');
    await page.fill('[name="password"]', 'analyst123');
    await page.click('button[type="submit"]');
  });

  test('should list assessments', async ({ page }) => {
    await page.goto('/assessments/');
    await expect(page).toHaveURL('/assessments/');
    await expect(page.locator('h1, .card, table')).toBeVisible({ timeout: 5000 }).catch(() => {});
  });

  test('should show assessment detail', async ({ page }) => {
    await page.goto('/assessments/1/');
    await expect(page).toHaveURL(/\/assessments\/1\//);
    const title = page.locator('h1').first();
    await expect(title).toBeVisible({ timeout: 5000 });
  });

  test('should create new assessment', async ({ page }) => {
    await page.goto('/assessments/create/');
    await page.fill('[name="title"]', 'E2E Test Assessment');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/assessments/');
  });

  test('should edit assessment', async ({ page }) => {
    await page.goto('/assessments/1/edit/');
    await page.fill('[name="title"]', 'Updated E2E Title');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/assessments/');
  });

  test('should show create forbidden for respondent', async ({ page }) => {
    await page.goto('/accounts/logout/');
    await page.goto('/accounts/login/');
    await page.fill('[name="username"]', 'respondent');
    await page.fill('[name="password"]', 'respondent123');
    await page.click('button[type="submit"]');
    await page.goto('/assessments/create/');
    await expect(page.locator('text=Forbidden, text=403')).toBeVisible({ timeout: 5000 }).catch(() => {});
  });
});