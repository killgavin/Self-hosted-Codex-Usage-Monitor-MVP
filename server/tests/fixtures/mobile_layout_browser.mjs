import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const dashboardUrl = process.env.DASHBOARD_URL;
if (!dashboardUrl) throw new Error("DASHBOARD_URL is required");

const launchOptions = process.env.CHROMIUM_EXECUTABLE
  ? { executablePath: process.env.CHROMIUM_EXECUTABLE }
  : {};
const browser = await chromium.launch(launchOptions);
try {
  const page = await browser.newPage({ viewport: { width: 360, height: 800 } });
  await page.goto(dashboardUrl, { waitUntil: "networkidle" });
  await page.evaluate(async () => {
    const { renderRateLimitCards } = await import("/assets/app.mjs");
    renderRateLimitCards(document, document.getElementById("rate-limit-list"), [
      {
        id: "very-long-unknown-limit-identifier-that-must-wrap-without-horizontal-overflow",
        name: null,
        primary: {
          usedPercent: "12.345678901234567890",
          remainingPercent: "87.654321098765432110",
          windowDurationMinutes: 42,
          resetAt: "2023-11-14T22:13:20Z",
        },
        secondary: null,
      },
    ]);
  });
  const metrics = await page.evaluate(() => {
    const root = document.documentElement;
    const body = document.body;
    const shell = document.getElementById("dashboard-shell");
    return {
      viewportWidth: window.innerWidth,
      rootClientWidth: root.clientWidth,
      rootScrollWidth: root.scrollWidth,
      bodyClientWidth: body.clientWidth,
      bodyScrollWidth: body.scrollWidth,
      shellRight: shell.getBoundingClientRect().right,
    };
  });
  if (metrics.viewportWidth !== 360) throw new Error(`unexpected viewport: ${JSON.stringify(metrics)}`);
  if (metrics.rootScrollWidth > metrics.rootClientWidth) throw new Error(`root overflow: ${JSON.stringify(metrics)}`);
  if (metrics.bodyScrollWidth > metrics.bodyClientWidth) throw new Error(`body overflow: ${JSON.stringify(metrics)}`);
  if (metrics.shellRight > metrics.viewportWidth) throw new Error(`shell overflow: ${JSON.stringify(metrics)}`);
  console.log(`mobile-layout: PASS ${JSON.stringify(metrics)}`);
} finally {
  await browser.close();
}
