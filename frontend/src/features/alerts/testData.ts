import type { AlertDetail } from "../../api/schema";

export const alertDetail: AlertDetail = {
  id: "a1", transactionId: "t1", probability: 0.96, riskBand: "critical",
  amount: "800.00", currency: "USD", merchantRef: "MERCHANT-001",
  channel: "ecommerce", country: "GB", status: "open", createdAt: "2026-07-27T14:00:00Z",
  transaction: { id: "t1", eventTime: "2026-07-27T14:00:00Z", accountId: "acct",
    merchantId: "merchant", amount: "800.00", currency: "USD", channel: "ecommerce",
    country: "GB", region: "LND", deviceId: "device", ipHash: "0123456789abcdef" },
  score: { id: "s1", probability: 0.96, riskBand: "critical", threshold: 0.8,
    modelVersion: "test-v1", featureVersion: "1.0.0", scoredAt: "2026-07-27T14:00:01Z",
    explanationStatus: "available", factors: [{ feature: "velocity", label: "Recent velocity", direction: "higher", contribution: 0.8 }] },
  history: [{ id: "h1", eventType: "created", fromStatus: null, toStatus: "open", actorRef: "system", createdAt: "2026-07-27T14:00:01Z" }],
  decisions: [{ id: "d1", alertId: "a1", outcome: "needs_review", note: "Check device", reviewerRef: "demo-analyst", createdAt: "2026-07-27T14:02:00Z" }],
  explanationDisclaimer: "Model factors indicate statistical influence, not proof or cause of fraud.",
};
