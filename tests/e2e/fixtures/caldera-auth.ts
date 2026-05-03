import { test as base, expect, type Page } from "@playwright/test";

const CALDERA_USER = process.env.CALDERA_USER || "admin";
const CALDERA_PASS = process.env.CALDERA_PASS || "admin";

/**
 * Authenticate against the Caldera login page.
 * Handles both the Vue/magma login form and basic-auth style login.
 */
async function authenticateCaldera(page: Page, baseURL: string) {
  await page.goto(baseURL);

  // If already on the main page (no login required), return early
  const url = page.url();
  if (!url.includes("/login") && !url.includes("/enter")) {
    const appShell = page.locator("#app, .main-content, nav.navbar");
    try {
      await appShell.first().waitFor({ timeout: 5_000 });
      return;
    } catch {
      // Fall through to login
    }
  }

  // Wait for any login form to appear
  const usernameField = page.locator(
    'input[name="username"], input[type="text"]#username, input[placeholder*="user" i]'
  );
  const passwordField = page.locator(
    'input[name="password"], input[type="password"]'
  );

  await usernameField.first().waitFor({ timeout: 10_000 });
  await usernameField.first().fill(CALDERA_USER);
  await passwordField.first().fill(CALDERA_PASS);

  // Submit
  const submitBtn = page.locator(
    'button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in")'
  );
  await submitBtn.first().click();

  // Wait for navigation away from login
  await page.waitForURL((url) => !url.pathname.includes("/login"), {
    timeout: 15_000,
  });
}

type CalderaFixtures = {
  authenticatedPage: Page;
};

export const test = base.extend<CalderaFixtures>({
  authenticatedPage: async ({ page, baseURL }, use) => {
    await authenticateCaldera(page, baseURL!);
    await use(page);
  },
});

export { expect };
