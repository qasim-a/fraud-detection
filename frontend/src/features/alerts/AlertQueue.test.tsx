import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import type { FraudApi } from "../../api/client";
import { AlertQueue } from "./AlertQueue";
import { alertDetail } from "./testData";

function client(listAlerts: FraudApi["listAlerts"]): FraudApi {
  return { listAlerts, getAlert: vi.fn(), updateAlertStatus: vi.fn(), createDecision: vi.fn() };
}

describe("AlertQueue", () => {
  it("loads risk-prioritized alerts and exposes filtering", async () => {
    const listAlerts = vi.fn().mockResolvedValue({ items: [alertDetail] });
    render(<MemoryRouter><AlertQueue client={client(listAlerts)} /></MemoryRouter>);
    expect(screen.getByRole("status")).toHaveTextContent("Loading alerts");
    expect(await screen.findByText("MERCHANT-001")).toBeVisible();
    expect(screen.getByRole("combobox", { name: "Status" })).toHaveValue("open");
    fireEvent.change(screen.getByRole("combobox", { name: "Minimum risk" }), { target: { value: "0.9" } });
    await waitFor(() => expect(listAlerts).toHaveBeenLastCalledWith(expect.objectContaining({ minRisk: 0.9 })));
  });

  it("shows an actionable empty state", async () => {
    render(<MemoryRouter><AlertQueue client={client(vi.fn().mockResolvedValue({ items: [] }))} /></MemoryRouter>);
    expect(await screen.findByText("No alerts match these filters")).toBeVisible();
    expect(screen.getByRole("button", { name: "Reset filters" })).toBeVisible();
  });

  it("shows API failures", async () => {
    render(<MemoryRouter><AlertQueue client={client(vi.fn().mockRejectedValue(new Error("offline")))} /></MemoryRouter>);
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("offline"));
  });
});
