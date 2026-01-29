import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('loads and shows stats cards', async ({ page }) => {
    await page.goto('/');
    // Wait for React to mount something (blank white page => app didn't render yet)
    await expect(page.getByRole('heading', { name: 'Job Search Dashboard' })).toBeVisible({ timeout: 20000 });

    // Backend calls can be slow on first boot; wait for either stats response or the error UI.
    await Promise.race([
      page.waitForResponse((r) => r.url().includes('/api/dashboard/stats') && r.status() === 200, { timeout: 20000 }),
      page.getByText(/Error loading data/i).waitFor({ timeout: 20000 }),
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

