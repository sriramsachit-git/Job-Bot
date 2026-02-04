import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('loads and shows stats cards', async ({ page }) => {
    await page.goto('/');
    // Wait for React to mount
    await expect(page.getByRole('heading', { name: 'Job Search Dashboard' })).toBeVisible({ timeout: 20000 });

    // Wait for either success (stats cards) or error UI; avoid depending on exact 200 response timing
    await Promise.race([
      page.getByText('Total Jobs').waitFor({ state: 'visible', timeout: 30000 }),
      page.getByText(/Error loading data/i).waitFor({ state: 'visible', timeout: 30000 }),
    ]);

    await expect(page.getByText('Total Jobs')).toBeVisible();
    await expect(page.getByText('Applied')).toBeVisible();
    await expect(page.getByText('Pending Review')).toBeVisible();
    await expect(page.getByText('Resumes Generated')).toBeVisible();
  });

  test('navigates to New Search', async ({ page }) => {
    await page.goto('/');
    await page.getByText('New Search').click();
    await expect(page).toHaveURL(/\/search\/new/);
    await expect(page.getByText('New Job Search')).toBeVisible();
  });
});

