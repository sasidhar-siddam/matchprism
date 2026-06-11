// One-off: screenshot the World Cup pages from the static export.
// Usage: node scripts/screenshot_worldcup.mjs
import { chromium } from "@playwright/test";
import fs from "fs";

const BASE = "http://localhost:4173";
const OUT_DIR = "screenshots";
const PAGES = [
  { url: "/worldcup.html", name: "worldcup-hub", fullPage: true },
  { url: "/worldcup/matches.html", name: "worldcup-matches", fullPage: false },
  { url: "/worldcup/news.html", name: "worldcup-news", fullPage: true },
  {
    url: "/worldcup/news/mexico-south-africa-world-cup-recap-2026-06-11.html",
    name: "worldcup-article",
    fullPage: true,
  },
];

fs.mkdirSync(OUT_DIR, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

for (const p of PAGES) {
  await page.goto(BASE + p.url, { waitUntil: "networkidle" });
  await page.waitForTimeout(400);
  const file = `${OUT_DIR}/${p.name}.png`;
  await page.screenshot({ path: file, fullPage: p.fullPage });
  console.log("saved", file);
}

await browser.close();
