#!/usr/bin/env node
// Genera el banner (2560x1440) y el avatar (800x800) del canal en canal/.
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
(async () => {
  const out = path.resolve(__dirname, "../canal");
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 2560, height: 1440 } });
  await page.goto("file://" + path.join(__dirname, "brand.html"));
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(out, "banner.jpg"), type: "jpeg", quality: 92 });
  await page.evaluate(() => { document.getElementById("b").style.display = "none"; document.getElementById("a").style.display = "block"; });
  await page.setViewportSize({ width: 800, height: 800 });
  await page.screenshot({ path: path.join(out, "avatar.png") });
  await browser.close();
})();
