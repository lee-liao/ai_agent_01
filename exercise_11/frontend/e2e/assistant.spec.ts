import { test, expect } from '@playwright/test';

test('coach conversation produces advice with supportive structure', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Get Started' }).click();

  // On /coach
  await page.getByLabel('Your name').fill('Parent QA');
  await page.getByRole('button', { name: 'Start Coaching' }).click();

  // On /coach/chat
  await page.getByRole('button', { name: 'Start Session' }).click();

  // Send a message
  const input = page.getByPlaceholder(/routines|Start session to chat|Ask about/);
  await input.fill('How to handle bedtime resistance?');
  await page.keyboard.press('Enter');

  // Expect a coach advice bubble to appear
  await expect(page.getByText('Here are a few ideas you might try', { exact: false })).toBeVisible();
});
