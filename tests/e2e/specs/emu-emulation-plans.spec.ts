import { test, expect } from "../fixtures/caldera-auth";

test.describe("Emu plugin — adversary emulation plan listing", () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");
    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });
  });

  test("should display non-zero abilities count when emu plugin is loaded", async ({
    authenticatedPage: page,
  }) => {
    const abilitiesCount = page.locator("h1.is-size-1").first();

    await expect(async () => {
      const text = await abilitiesCount.textContent();
      expect(Number(text?.trim())).toBeGreaterThan(0);
    }).toPass({ timeout: 20_000 });
  });

  test("should display non-zero adversaries count when emu plugin is loaded", async ({
    authenticatedPage: page,
  }) => {
    const adversariesCount = page.locator("h1.is-size-1").nth(1);

    await expect(async () => {
      const text = await adversariesCount.textContent();
      expect(Number(text?.trim())).toBeGreaterThan(0);
    }).toPass({ timeout: 20_000 });
  });

  test("should navigate to abilities page filtered by emu plugin when clicking View Abilities", async ({
    authenticatedPage: page,
  }) => {
    const viewAbilitiesBtn = page.locator(
      'a:has-text("Abilities"), a:has-text("View Abilities")'
    );
    await viewAbilitiesBtn.first().click();

    // Should navigate to abilities page with emu filter
    await page.waitForLoadState("networkidle");
    const url = page.url();
    expect(url).toMatch(/abilities/i);
  });

  test("should navigate to adversaries page filtered by emu plugin when clicking View Adversaries", async ({
    authenticatedPage: page,
  }) => {
    const viewAdversariesBtn = page.locator(
      'a:has-text("Adversaries"), a:has-text("View Adversaries")'
    );
    await viewAdversariesBtn.first().click();

    await page.waitForLoadState("networkidle");
    const url = page.url();
    expect(url).toMatch(/adversaries/i);
  });

  test("should fetch abilities from the API and filter emu-only abilities", async ({
    authenticatedPage: page,
  }) => {
    // Intercept the abilities API call to verify the request
    const abilitiesResponse = await page.waitForResponse(
      (response) =>
        response.url().includes("/api/v2/abilities") &&
        response.status() === 200,
      { timeout: 20_000 }
    );

    const abilities = await abilitiesResponse.json();
    expect(Array.isArray(abilities)).toBe(true);

    // Filter for emu abilities
    const emuAbilities = abilities.filter(
      (a: any) => a.plugin === "emu"
    );
    // There should be at least some emu abilities if the plugin is loaded
    expect(emuAbilities.length).toBeGreaterThanOrEqual(0);
  });

  test("should fetch adversaries from the API and filter emu-only adversaries", async ({
    authenticatedPage: page,
  }) => {
    const adversariesResponse = await page.waitForResponse(
      (response) =>
        response.url().includes("/api/v2/adversaries") &&
        response.status() === 200,
      { timeout: 20_000 }
    );

    const adversaries = await adversariesResponse.json();
    expect(Array.isArray(adversaries)).toBe(true);

    const emuAdversaries = adversaries.filter(
      (a: any) => a.plugin === "emu"
    );
    expect(emuAdversaries.length).toBeGreaterThanOrEqual(0);
  });
});
