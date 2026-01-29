import { test, expect } from '@playwright/test';

test.describe('API Connectivity', () => {
  test('backend health endpoint', async ({ request }) => {
    const res = await request.get('http://localhost:8000/health');
    expect(res.status()).toBe(200);
    expect(await res.json()).toEqual({ status: 'healthy' });
  });

  test('dashboard stats endpoint', async ({ request }) => {
    const res = await request.get('http://localhost:8000/api/dashboard/stats');
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('total_jobs');
    expect(body).toHaveProperty('applied');
    expect(body).toHaveProperty('pending');
    expect(body).toHaveProperty('resumes_generated');
  });
});

