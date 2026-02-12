// @ts-check
import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');

  // Expect a title "to contain" a substring.
  // Note: Adjust this expectation based on your actual app title
  await expect(page).toHaveTitle(/Ops Agent/);
});

test('should show main welcome content', async ({ page }) => {
  await page.goto('/');

  // Check for the specific welcome text from your project
  await expect(page.getByText('我是您的运维智能助手')).toBeVisible();
  
  // Note: "Upload Knowledge Base" button is only visible for logged-in users.
  // Since we are running in a fresh context (guest), we skip this check.
  // await expect(page.getByRole('button', { name: '上传知识库' })).toBeVisible();
});
