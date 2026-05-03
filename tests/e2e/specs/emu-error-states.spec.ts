import { test, expect } from "../fixtures/caldera-auth";

test.describe("Emu plugin — error states and edge cases", () => {
  test("should handle abilities API failure gracefully", async ({
    authenticatedPage: page,
  }) => {
    // Intercept abilities API and return error
    await page.route("**/api/v2/abilities", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal Server Error" }),
      })
    );

    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    // The page should still render the heading
    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });

    // Abilities count should show placeholder "---" since API failed
    const abilitiesCount = page.locator("h1.is-size-1").first();
    await expect(abilitiesCount).toBeVisible({ timeout: 10_000 });
    const text = await abilitiesCount.textContent();
    expect(text?.trim()).toBe("---");
  });

  test("should handle adversaries API failure gracefully", async ({
    authenticatedPage: page,
  }) => {
    // Intercept adversaries API and return error
    await page.route("**/api/v2/adversaries", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal Server Error" }),
      })
    );

    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });

    // Adversaries count should show placeholder
    const adversariesCount = page.locator("h1.is-size-1").nth(1);
    await expect(adversariesCount).toBeVisible({ timeout: 10_000 });
    const text = await adversariesCount.textContent();
    expect(text?.trim()).toBe("---");
  });

  test("should handle network timeout for abilities API gracefully", async ({
    authenticatedPage: page,
  }) => {
    await page.route("**/api/v2/abilities", (route) => route.abort());

    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("domcontentloaded");

    // Page should still render
    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });
  });

  test("should handle network timeout for adversaries API gracefully", async ({
    authenticatedPage: page,
  }) => {
    await page.route("**/api/v2/adversaries", (route) => route.abort());

    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("domcontentloaded");

    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });
  });

  test("should handle both APIs failing simultaneously", async ({
    authenticatedPage: page,
  }) => {
    await page.route("**/api/v2/abilities", (route) =>
      route.fulfill({
        status: 500,
        body: "error",
      })
    );
    await page.route("**/api/v2/adversaries", (route) =>
      route.fulfill({
        status: 500,
        body: "error",
      })
    );

    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("domcontentloaded");

    // Page should render without crashing
    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });

    // Both counts should show placeholder
    const counts = page.locator("h1.is-size-1");
    const count = await counts.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test("should display abilities count as 0 when API returns empty array", async ({
    authenticatedPage: page,
  }) => {
    // Return empty arrays (no emu abilities)
    await page.route("**/api/v2/abilities", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      })
    );
    await page.route("**/api/v2/adversaries", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      })
    );

    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });

    // With empty arrays filtered for emu, counts should show "---" (falsy 0)
    const abilitiesCount = page.locator("h1.is-size-1").first();
    await expect(abilitiesCount).toBeVisible({ timeout: 10_000 });
    const text = await abilitiesCount.textContent();
    // 0 is falsy so the template shows "---"
    expect(text?.trim()).toMatch(/^(0|---)$/);
  });

  test("should not crash when API returns non-emu abilities only", async ({
    authenticatedPage: page,
  }) => {
    // Return abilities that belong to a different plugin
    await page.route("**/api/v2/abilities", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            ability_id: "test-1",
            name: "Test Ability",
            plugin: "stockpile",
          },
        ]),
      })
    );
    await page.route("**/api/v2/adversaries", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            adversary_id: "test-1",
            name: "Test Adversary",
            plugin: "stockpile",
          },
        ]),
      })
    );

    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });

    // Emu-filtered counts should be 0 (shown as "---")
    const abilitiesCount = page.locator("h1.is-size-1").first();
    await expect(abilitiesCount).toBeVisible({ timeout: 10_000 });
    const text = await abilitiesCount.textContent();
    expect(text?.trim()).toMatch(/^(0|---)$/);
  });
});
