import { test, expect } from "../fixtures/caldera-auth";

test.describe("Emu plugin — page load and accessibility", () => {
  test("should load the Caldera UI and find Emu in the plugin navigation", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/");

    const emuLink = page.locator(
      'a[href*="emu"], a:has-text("emu"), [data-plugin="emu"], nav >> text=emu'
    );
    await expect(emuLink.first()).toBeVisible({ timeout: 15_000 });
  });

  test("should navigate to the Emu plugin page", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const heading = page.locator("h2:has-text('Emu')");
    await expect(heading).toBeVisible({ timeout: 15_000 });
  });

  test("should display the plugin description text", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const description = page.locator(
      "text=Adversary Emulation Plans, text=CTID Adversary Emulation"
    );
    await expect(description.first()).toBeVisible({ timeout: 15_000 });
  });

  test("should display the abilities count card", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const abilitiesLabel = page.locator("p:has-text('abilities')").first();
    await expect(abilitiesLabel).toBeVisible({ timeout: 15_000 });
  });

  test("should display the adversaries count card", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const adversariesLabel = page
      .locator("p:has-text('adversaries')")
      .first();
    await expect(adversariesLabel).toBeVisible({ timeout: 15_000 });
  });

  test("should show numeric counts for abilities (not just placeholder)", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    // Wait for the abilities count to load (should be a number, not "---")
    const abilitiesCount = page.locator("h1.is-size-1").first();
    await expect(abilitiesCount).toBeVisible({ timeout: 15_000 });

    // The count should eventually become a number
    await expect(async () => {
      const text = await abilitiesCount.textContent();
      expect(text?.trim()).not.toBe("---");
      expect(Number(text?.trim())).toBeGreaterThanOrEqual(0);
    }).toPass({ timeout: 15_000 });
  });

  test("should show numeric counts for adversaries (not just placeholder)", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    // The adversaries count is the second h1.is-size-1
    const adversariesCount = page.locator("h1.is-size-1").nth(1);
    await expect(adversariesCount).toBeVisible({ timeout: 15_000 });

    await expect(async () => {
      const text = await adversariesCount.textContent();
      expect(text?.trim()).not.toBe("---");
      expect(Number(text?.trim())).toBeGreaterThanOrEqual(0);
    }).toPass({ timeout: 15_000 });
  });

  test("should have a View Abilities button/link", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const viewAbilitiesBtn = page.locator(
      'a:has-text("Abilities"), button:has-text("Abilities"), a:has-text("View Abilities")'
    );
    await expect(viewAbilitiesBtn.first()).toBeVisible({ timeout: 15_000 });
  });

  test("should have a View Adversaries button/link", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/#/plugins/emu");
    await page.waitForLoadState("networkidle");

    const viewAdversariesBtn = page.locator(
      'a:has-text("Adversaries"), button:has-text("Adversaries"), a:has-text("View Adversaries")'
    );
    await expect(viewAdversariesBtn.first()).toBeVisible({ timeout: 15_000 });
  });
});
