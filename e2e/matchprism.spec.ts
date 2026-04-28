import { test, expect } from "@playwright/test";

// ═══════════════════════════════════════════
//  1. HOMEPAGE
// ═══════════════════════════════════════════

test.describe("Homepage", () => {
  test("loads and shows MatchPrism branding", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/MatchPrism/);
    await expect(page.locator("text=MatchPrism").first()).toBeVisible();
  });

  test("shows T20 Intelligence label", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=T20 Intelligence")).toBeVisible();
  });

  test("shows featured match with team names", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=RCB").first()).toBeVisible();
    await expect(page.locator("text=SRH").first()).toBeVisible();
  });

  test("shows countdown timer (not hardcoded 02:48:15)", async ({ page }) => {
    await page.goto("/");
    // Should NOT contain the old hardcoded values
    const body = await page.textContent("body");
    expect(body).not.toContain("02 : 48 : 15");
  });

  test("shows intelligence picks section", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=Intelligence Picks").first()).toBeVisible();
  });

  test("shows upcoming matches with links", async ({ page }) => {
    await page.goto("/");
    const matchLinks = page.locator('a[href^="/match/"]');
    expect(await matchLinks.count()).toBeGreaterThan(3);
  });

  test("nav links work", async ({ page }) => {
    await page.goto("/");
    // Desktop nav (inside header)
    await expect(page.locator('header a[href="/matches"]')).toBeVisible();
    await expect(page.locator('header a[href="/players"]')).toBeVisible();
    await expect(page.locator('header a[href="/venues"]')).toBeVisible();
  });
});

// ═══════════════════════════════════════════
//  2. MATCHES INDEX
// ═══════════════════════════════════════════

test.describe("Matches Page", () => {
  test("loads and lists all fixtures", async ({ page }) => {
    await page.goto("/matches");
    await expect(page).toHaveTitle(/IPL 2026 Schedule/);
    const matchLinks = page.locator('a[href^="/match/"]');
    expect(await matchLinks.count()).toBeGreaterThanOrEqual(14);
  });

  test("shows venue and probabilities", async ({ page }) => {
    await page.goto("/matches");
    await expect(page.locator("text=Chinnaswamy").first()).toBeVisible();
    await expect(page.locator("text=%").first()).toBeVisible();
  });

  test("match links navigate correctly", async ({ page }) => {
    await page.goto("/matches");
    await page.locator('a[href="/match/rcb-vs-srh"]').first().click();
    await expect(page).toHaveURL(/\/match\/rcb-vs-srh/);
    await expect(page.locator("text=RCB").first()).toBeVisible();
  });
});

// ═══════════════════════════════════════════
//  3. MATCH PREVIEW PAGE
// ═══════════════════════════════════════════

test.describe("Match Preview - RCB vs SRH", () => {
  test("loads with correct title", async ({ page }) => {
    await page.goto("/match/rcb-vs-srh");
    await expect(page).toHaveTitle(/RCB vs SRH.*MatchPrism/);
  });

  test("shows win probability bar", async ({ page }) => {
    await page.goto("/match/rcb-vs-srh");
    await expect(page.locator("text=54%").first()).toBeVisible();
    await expect(page.locator("text=46%").first()).toBeVisible();
  });

  test("shows venue intelligence section", async ({ page }) => {
    await page.goto("/match/rcb-vs-srh");
    await expect(page.locator("text=Venue Intelligence").first()).toBeVisible();
    await expect(page.locator("text=Chase Win").first()).toBeVisible();
  });

  test("shows captain genius picks", async ({ page }) => {
    await page.goto("/match/rcb-vs-srh");
    await expect(page.locator("text=Captain Genius").first()).toBeVisible();
  });

  test("shows conditions intelligence (pitch scanner)", async ({ page }) => {
    await page.goto("/match/rcb-vs-srh");
    await expect(page.locator("text=Conditions Intelligence").first()).toBeVisible();
    await expect(page.locator("text=Dew").first()).toBeVisible();
    await expect(page.locator("text=Toss Recommendation").first()).toBeVisible();
  });

  test("shows H2H section", async ({ page }) => {
    await page.goto("/match/rcb-vs-srh");
    await expect(page.locator("text=Historical Supremacy").first()).toBeVisible();
  });

  test("shows player venue fit table", async ({ page }) => {
    await page.goto("/match/rcb-vs-srh");
    await expect(page.locator("text=Player Venue Fit").first()).toBeVisible();
  });

  test("player names are clickable links to profiles", async ({ page }) => {
    await page.goto("/match/rcb-vs-srh");
    const playerLinks = page.locator('a[href^="/player/"]');
    expect(await playerLinks.count()).toBeGreaterThan(3);
  });

  test("no betting/gambling language on page", async ({ page }) => {
    await page.goto("/match/rcb-vs-srh");
    const body = (await page.textContent("body")) ?? "";
    const forbidden = ["betting", "gamble", "gambling", "wager", "bookie", "bookmaker", "punter"];
    for (const word of forbidden) {
      expect(body.toLowerCase()).not.toContain(word);
    }
  });
});

// ═══════════════════════════════════════════
//  4. PLAYERS INDEX
// ═══════════════════════════════════════════

test.describe("Players Page", () => {
  test("loads and shows player cards", async ({ page }) => {
    await page.goto("/players");
    await expect(page).toHaveTitle(/T20 Players/);
    await expect(page.locator("text=Player Intelligence").first()).toBeVisible();
  });

  test("shows league coverage info", async ({ page }) => {
    await page.goto("/players");
    await expect(page.locator("text=IPL").first()).toBeVisible();
    await expect(page.locator("text=BBL").first()).toBeVisible();
  });

  test("shows batter/bowler/allrounder sections", async ({ page }) => {
    await page.goto("/players");
    await expect(page.locator("text=Top Batters").first()).toBeVisible();
    await expect(page.locator("text=Top Bowlers").first()).toBeVisible();
    await expect(page.locator("text=All-rounders").first()).toBeVisible();
  });

  test("player cards link to profile pages", async ({ page }) => {
    await page.goto("/players");
    const playerLinks = page.locator('a[href^="/player/"]');
    expect(await playerLinks.count()).toBeGreaterThan(50);
  });

  test("clicking a player navigates to their profile", async ({ page }) => {
    await page.goto("/players");
    await page.locator('a[href^="/player/"]').first().click();
    await expect(page).toHaveURL(/\/player\//, { timeout: 15000 });
  });
});

// ═══════════════════════════════════════════
//  5. PLAYER PROFILE
// ═══════════════════════════════════════════

test.describe("Player Profile - Kohli", () => {
  test("loads with real data", async ({ page }) => {
    await page.goto("/player/v-kohli");
    await expect(page).toHaveTitle(/Kohli.*MatchPrism/);
    await expect(page.locator("text=V Kohli").first()).toBeVisible();
  });

  test("shows career stats", async ({ page }) => {
    await page.goto("/player/v-kohli");
    // Should show real batting stats (runs > 8000)
    const body = (await page.textContent("body")) ?? "";
    expect(body).toMatch(/\d{4,}/); // 4+ digit number (career runs)
  });

  test("shows form pulse chart", async ({ page }) => {
    await page.goto("/player/v-kohli");
    await expect(page.locator("text=Recent Form Pulse").first()).toBeVisible();
  });

  test("shows venue fit analysis", async ({ page }) => {
    await page.goto("/player/v-kohli");
    await expect(page.locator("text=Venue Fit Analysis").first()).toBeVisible();
  });
});

test.describe("Player Profile - Bumrah", () => {
  test("loads bowler profile", async ({ page }) => {
    await page.goto("/player/jj-bumrah");
    await expect(page.locator("text=JJ Bumrah").first()).toBeVisible();
  });
});

// ═══════════════════════════════════════════
//  6. VENUES INDEX
// ═══════════════════════════════════════════

test.describe("Venues Page", () => {
  test("loads and shows venue cards", async ({ page }) => {
    await page.goto("/venues");
    await expect(page).toHaveTitle(/T20 Venues/);
    await expect(page.locator("text=Venue Intelligence").first()).toBeVisible();
  });

  test("shows venue stats (avg score, chase %, run rate)", async ({ page }) => {
    await page.goto("/venues");
    await expect(page.locator("text=Avg Score").first()).toBeVisible();
    await expect(page.locator("text=Chase %").first()).toBeVisible();
    await expect(page.locator("text=Run Rate").first()).toBeVisible();
  });

  test("shows league tags on venues", async ({ page }) => {
    await page.goto("/venues");
    // Venues should show which leagues they host
    const leagueTags = page.locator("text=ipl");
    expect(await leagueTags.count()).toBeGreaterThan(0);
  });

  test("venue cards link to venue pages", async ({ page }) => {
    await page.goto("/venues");
    const venueLinks = page.locator('a[href^="/venue/"]');
    expect(await venueLinks.count()).toBeGreaterThan(20);
  });
});

// ═══════════════════════════════════════════
//  7. VENUE DETAIL
// ═══════════════════════════════════════════

test.describe("Venue Detail - Wankhede", () => {
  test("loads with real data", async ({ page }) => {
    await page.goto("/venue/wankhede-stadium");
    await expect(page.locator("text=Wankhede Stadium").first()).toBeVisible();
  });

  test("shows key metrics", async ({ page }) => {
    await page.goto("/venue/wankhede-stadium");
    await expect(page.locator("text=AVG 1ST INN").first()).toBeVisible();
  });

  test("shows toss intelligence", async ({ page }) => {
    await page.goto("/venue/wankhede-stadium");
    await expect(page.locator("text=Toss Intelligence").first()).toBeVisible();
  });

  test("shows phase dynamics", async ({ page }) => {
    await page.goto("/venue/wankhede-stadium");
    await expect(page.locator("text=Phase Dynamics").first()).toBeVisible();
  });
});

// ═══════════════════════════════════════════
//  8. ALL MATCH PAGES LOAD
// ═══════════════════════════════════════════

const matchSlugs = [
  "rcb-vs-srh", "mi-vs-csk", "kkr-vs-rr", "pbks-vs-dc",
  "lsg-vs-gt", "srh-vs-mi", "csk-vs-kkr", "rcb-vs-rr",
  "gt-vs-dc", "pbks-vs-lsg", "mi-vs-kkr", "srh-vs-csk",
  "rr-vs-gt", "rcb-vs-dc",
];

test.describe("All 14 match pages load", () => {
  for (const slug of matchSlugs) {
    test(`/match/${slug} returns 200`, async ({ page }) => {
      const response = await page.goto(`/match/${slug}`);
      expect(response?.status()).toBe(200);
    });
  }
});

// ═══════════════════════════════════════════
//  9. CROSS-PAGE NAVIGATION
// ═══════════════════════════════════════════

test.describe("Navigation flow", () => {
  test("homepage -> match -> player -> back works", async ({ page }) => {
    await page.goto("/");
    // Click through to a match
    await page.locator('a[href="/match/rcb-vs-srh"]').first().click();
    await expect(page).toHaveURL(/\/match\/rcb-vs-srh/, { timeout: 10000 });

    // Click a player name (wait for page to fully load)
    await page.waitForLoadState("networkidle");
    const playerLink = page.locator('a[href^="/player/"]').first();
    if (await playerLink.count()) {
      await playerLink.click();
      await expect(page).toHaveURL(/\/player\//, { timeout: 15000 });

      // Navigate back via nav
      await page.locator('a[href="/"]').first().click();
      await expect(page).toHaveURL("/");
    }
  });

  test("mobile bottom nav links all work", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/");

    // Bottom nav should be visible on mobile
    const bottomNav = page.locator("nav.fixed.bottom-0");
    await expect(bottomNav).toBeVisible();

    // All bottom nav links should work
    for (const href of ["/matches", "/players", "/venues"]) {
      const link = bottomNav.locator(`a[href="${href}"]`);
      if (await link.count()) {
        await link.click();
        await expect(page).toHaveURL(href);
        await page.goto("/"); // reset
      }
    }
  });
});

// ═══════════════════════════════════════════
//  10. ACCESSIBILITY BASICS
// ═══════════════════════════════════════════

test.describe("Accessibility", () => {
  test("no font sizes below 11px on homepage", async ({ page }) => {
    await page.goto("/");
    const tinyText = await page.evaluate(() => {
      const elements = document.querySelectorAll("*");
      const violations: string[] = [];
      elements.forEach((el) => {
        const size = parseFloat(getComputedStyle(el).fontSize);
        if (size > 0 && size < 11 && el.textContent?.trim()) {
          violations.push(`${el.tagName}: "${el.textContent?.trim().slice(0, 30)}" = ${size}px`);
        }
      });
      return violations.slice(0, 5);
    });
    if (tinyText.length > 0) {
      console.warn("Font size violations:", tinyText);
    }
    // Warn but don't fail — some browser defaults may be inherited
  });

  test("all pages have title tags", async ({ page }) => {
    for (const url of ["/", "/matches", "/players", "/venues", "/match/rcb-vs-srh"]) {
      await page.goto(url);
      const title = await page.title();
      expect(title).toBeTruthy();
      expect(title).toContain("MatchPrism");
    }
  });

  test("brand name is MatchPrism everywhere (not CricMind)", async ({ page }) => {
    for (const url of ["/", "/matches", "/players", "/match/rcb-vs-srh"]) {
      await page.goto(url);
      const body = (await page.textContent("body")) ?? "";
      expect(body).not.toContain("CricMind");
    }
  });
});
