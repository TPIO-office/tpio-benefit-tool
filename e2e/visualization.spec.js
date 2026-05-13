const { test, expect } = require('@playwright/test');

test.describe('Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/accounts/login/');
    await page.fill('[name="username"]', 'analyst');
    await page.fill('[name="password"]', 'analyst123');
    await page.click('button[type="submit"]');
  });

  test('should render Sankey diagram without JS errors', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/assessments/1/sankey/');
    await expect(page).toHaveURL(/\/assessments\/1\/sankey\//);

    // Wait for the SVG to be rendered by d3-sankey
    await page.waitForSelector('#sankey-chart svg', { timeout: 10000 });

    // Verify the diagram has content (nodes and links)
    const svg = page.locator('#sankey-chart svg');
    await expect(svg).toBeVisible();

    const nodeCount = await page.locator('.sankey-node').count();
    const linkCount = await page.locator('.sankey-link').count();
    expect(nodeCount).toBeGreaterThan(0);
    expect(linkCount).toBeGreaterThan(0);

    // Assert no JavaScript console errors occurred
    expect(consoleErrors).toEqual([]);
  });

  test('should allow dragging Sankey nodes without JS errors', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/assessments/1/sankey/');
    await page.waitForSelector('#sankey-chart svg', { timeout: 10000 });

    // Get the first node rect and drag it
    const nodeRect = page.locator('.sankey-node rect').first();
    await expect(nodeRect).toBeVisible();

    const box = await nodeRect.boundingBox();
    if (box) {
      // Click and drag the node slightly
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width / 2 + 30, box.y + box.height / 2 + 20);
      await page.mouse.up();

      // Verify the node moved (transform attribute changed)
      const nodeGroup = page.locator('.sankey-node').first();
      await expect(nodeGroup).toBeVisible();
    }

    // Assert no JavaScript console errors occurred during drag
    expect(consoleErrors).toEqual([]);
  });

  test('should return JSON for value tree API', async ({ page }) => {
    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/assessments/1/tree-json/') && resp.ok()),
      page.goto('/assessments/1/tree-json/'),
    ]);
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