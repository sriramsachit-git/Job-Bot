import { test, expect } from '@playwright/test';

test.describe('Search flow', () => {
  test('can open search wizard', async ({ page }) => {
    await page.goto('/search/new');
    await expect(page.getByText('New Job Search')).toBeVisible();
  });
});

