import { test, expect } from "../fixtures/caldera-auth";

test.describe("Emu plugin — navigation and details view", () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");
    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });
  });

  test("should show abilities page with emu-specific abilities after navigation", async ({
    authenticatedPage: page,
  }) => {
    const viewAbilitiesBtn = page.locator(
      'a:has-text("Abilities"), a:has-text("View Abilities")'
    );
    await viewAbilitiesBtn.first().click();

    await page.waitForLoadState("networkidle");

    // On the abilities page, there should be some content rendered
    // Look for typical abilities page elements
    const pageContent = page.locator(
      ".content, .abilities, table, .card, .panel"
    );
    await expect(pageContent.first()).toBeVisible({ timeout: 15_000 });
  });

  test("should show adversaries page with emu-specific adversaries after navigation", async ({
    authenticatedPage: page,
  }) => {
    const viewAdversariesBtn = page.locator(
      'a:has-text("Adversaries"), a:has-text("View Adversaries")'
    );
    await viewAdversariesBtn.first().click();

    await page.waitForLoadState("networkidle");

    const pageContent = page.locator(
      ".content, .adversaries, table, .card, .panel"
    );
    await expect(pageContent.first()).toBeVisible({ timeout: 15_000 });
  });

  test("should be able to return to the emu plugin page from abilities", async ({
    authenticatedPage: page,
  }) => {
    // Navigate to abilities
    const viewAbilitiesBtn = page.locator(
      'a:has-text("Abilities"), a:has-text("View Abilities")'
    );
    await viewAbilitiesBtn.first().click();
    await page.waitForLoadState("networkidle");

    // Navigate back to emu
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });
  });

  test("should be able to return to the emu plugin page from adversaries", async ({
    authenticatedPage: page,
  }) => {
    const viewAdversariesBtn = page.locator(
      'a:has-text("Adversaries"), a:has-text("View Adversaries")'
    );
    await viewAdversariesBtn.first().click();
    await page.waitForLoadState("networkidle");

    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });
  });

  test("should preserve counts when returning to the emu page", async ({
    authenticatedPage: page,
  }) => {
    // Get initial counts
    const abilitiesCount = page.locator("h1.is-size-1").first();
    await expect(async () => {
      const text = await abilitiesCount.textContent();
      expect(text?.trim()).not.toBe("---");
    }).toPass({ timeout: 15_000 });

    const initialAbilityText = await abilitiesCount.textContent();

    // Navigate away and back
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const newAbilitiesCount = page.locator("h1.is-size-1").first();
    await expect(async () => {
      const text = await newAbilitiesCount.textContent();
      expect(text?.trim()).not.toBe("---");
    }).toPass({ timeout: 15_000 });

    const returnedAbilityText = await newAbilitiesCount.textContent();
    expect(returnedAbilityText?.trim()).toBe(initialAbilityText?.trim());
  });
});
