import { expect, test } from "@playwright/test";

const alertId = "11111111-1111-4111-8111-111111111111";
const now = "2026-07-27T12:00:00Z";

const summary = {
  id: alertId, transactionId: "22222222-2222-4222-8222-222222222222",
  probability: 0.97, riskBand: "critical", amount: "9500.00", currency: "USD",
  merchantRef: "synthetic-merchant-001", channel: "ecommerce", country: "GB",
  status: "open", createdAt: now,
};

test("analyst reviews the highest-risk alert without rewriting its score", async ({ page }) => {
  const decisions: Array<Record<string, unknown>> = [];
  await page.route("**/api/v1/alerts?**", (route) =>
    route.fulfill({ json: { items: [summary], nextCursor: null } }),
  );
  await page.route(`**/api/v1/alerts/${alertId}`, async (route) => {
    if (route.request().method() === "PATCH") return route.fulfill({ json: summary });
    return route.fulfill({ json: {
      ...summary,
      transaction: { id: summary.transactionId, eventTime: now, accountId: "synthetic-account-001", merchantId: "synthetic-merchant-001", amount: summary.amount, currency: "USD", channel: "ecommerce", country: "GB", region: "LND", deviceId: "synthetic-device", ipHash: "synthetic-hash" },
      score: { id: "33333333-3333-4333-8333-333333333333", probability: 0.97, riskBand: "critical", threshold: 0.8, modelVersion: "fraud-xgb-demo", featureVersion: "1.0.0", scoredAt: now, explanationStatus: "available", factors: [{ feature: "amount_ratio_30d", label: "Amount compared with recent activity", direction: "higher", contribution: 1.8 }] },
      explanationDisclaimer: "Model influence is not proof or cause of fraud.",
      history: [{ id: "44444444-4444-4444-8444-444444444444", eventType: "created", actorRef: "system", createdAt: now }],
      decisions,
    } });
  });
  await page.route(`**/api/v1/alerts/${alertId}/decisions`, async (route) => {
    const input = route.request().postDataJSON();
    decisions.push({ id: `${decisions.length + 5}5555555-5555-4555-8555-555555555555`, alertId, reviewerRef: "demo-analyst", createdAt: now, ...input });
    return route.fulfill({ json: decisions.at(-1) });
  });

  await page.goto("/alerts");
  await page.getByRole("link", { name: /97%/ }).click();
  await expect(page.getByText("Model influence is not proof or cause of fraud.")).toBeVisible();
  await expect(page.getByText("fraud-xgb-demo")).toBeVisible();
  await page.getByLabel("Decision").selectOption("needs_review");
  await page.getByLabel("Optional note").fill("Escalate for verification");
  await page.getByRole("button", { name: "Record decision" }).click();
  await expect(page.getByText("Escalate for verification")).toBeVisible();
  await page.getByLabel("Decision").selectOption("confirmed_fraud");
  await page.getByRole("button", { name: "Record decision" }).click();
  await expect(page.getByText("confirmed fraud", { exact: true })).toBeVisible();
  await expect(page.getByText("fraud-xgb-demo")).toBeVisible();
});
