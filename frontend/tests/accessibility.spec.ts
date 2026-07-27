import { expect, test } from "@playwright/test";

test("dashboard exposes landmarks and keyboard-reachable navigation", async ({ page }) => {
  await page.route("**/api/v1/dashboard/summary?**", (route) => route.fulfill({ json: {
    range: { start: "2026-07-01T00:00:00Z", end: "2026-08-01T00:00:00Z" },
    totals: { transactions: 20, alerts: 3, amountAtRisk: "1250.00" },
    riskBands: { low: 12, medium: 5, high: 2, critical: 1 },
    reviewOutcomes: { confirmed_fraud: 1, legitimate: 1, unlabeled: 1 },
    series: [{ bucket: "2026-07-27", transactions: 20, alerts: 3 }],
  } }));
  await page.route("**/api/v1/models/active", (route) => route.fulfill({ json: {
    version: "fraud-xgb-demo", featureVersion: "1.0.0", datasetId: "synthetic-dataset",
    threshold: 0.8, activatedAt: "2026-07-27T12:00:00Z",
    metrics: { precision: 0.8, recall: 0.75, prAuc: 0.84, truePositive: 3, falsePositive: 1, trueNegative: 15, falseNegative: 1, alertVolume: 4 },
  } }));
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Operations overview" })).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Dashboard" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Alert queue" })).toBeFocused();
  await expect(page.getByLabel("Daily transaction and alert volume")).toBeVisible();
  await expect(page.getByLabel("Counts by fraud risk band")).toBeVisible();
});
