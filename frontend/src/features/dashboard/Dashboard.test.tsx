import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { FraudApi } from "../../api/client";
import type { DashboardSummary, ModelSummary } from "../../api/schema";
import { Dashboard } from "./Dashboard";

const summary: DashboardSummary = {
  range: { start: "2026-07-01T00:00:00Z", end: "2026-08-01T00:00:00Z" },
  totals: { transactions: 12, alerts: 3, amountAtRisk: "2400.00" },
  riskBands: { low: 5, medium: 4, high: 2, critical: 1 },
  reviewOutcomes: { legitimate: 1, confirmed_fraud: 1, needs_review: 0, unlabeled: 1 },
  series: [{ bucket: "2026-07-27T00:00:00Z", transactions: 12, alerts: 3 }],
};
const model: ModelSummary = {
  version: "v1", featureVersion: "1.0.0", datasetId: "dataset-1", threshold: 0.8,
  metrics: { precision: 0.8, recall: 0.7, prAuc: 0.75, truePositive: 7, falsePositive: 2, trueNegative: 90, falseNegative: 3, alertVolume: 9 },
  activatedAt: "2026-07-27T00:00:00Z",
};

function client(dashboard: Promise<DashboardSummary>, activeModel: Promise<ModelSummary> = Promise.resolve(model)): FraudApi {
  return { listAlerts: vi.fn(), getAlert: vi.fn(), updateAlertStatus: vi.fn(), createDecision: vi.fn(), getDashboard: vi.fn(() => dashboard), getActiveModel: vi.fn(() => activeModel) };
}

describe("Dashboard", () => {
  it("renders accessible chart descriptions and reconciled metrics", async () => {
    render(<Dashboard client={client(Promise.resolve(summary))} />);
    expect(screen.getByText("Loading dashboard…")).toBeVisible();
    expect(await screen.findByText("2,400.00")).toBeVisible();
    expect(screen.getByRole("img", { name: "Daily transaction and alert volume" })).toBeVisible();
    expect(screen.getByRole("img", { name: "Counts by fraud risk band" })).toBeVisible();
    expect(screen.getByRole("table", { name: "Evaluation confusion counts" })).toBeVisible();
  });

  it("shows honest empty states", async () => {
    const empty = { ...summary, totals: { transactions: 0, alerts: 0, amountAtRisk: "0.00" }, series: [] };
    render(<Dashboard client={client(Promise.resolve(empty))} />);
    await waitFor(() => expect(screen.getAllByText("No observed data for this range.")).toHaveLength(3));
  });

  it("shows dashboard and model-evaluation failures", async () => {
    render(<Dashboard client={client(Promise.reject(new Error("offline")), Promise.reject(new Error("no labels")))} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("offline");
    expect(await screen.findByText(/no complete labeled evaluation/i)).toBeVisible();
  });
});
