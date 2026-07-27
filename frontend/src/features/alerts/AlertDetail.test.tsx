import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import type { FraudApi } from "../../api/client";
import { AlertDetail } from "./AlertDetail";
import { alertDetail } from "./testData";

describe("AlertDetail", () => {
  it("labels factors as influence and preserves decision history", async () => {
    const client: FraudApi = {
      listAlerts: vi.fn(), getAlert: vi.fn().mockResolvedValue(alertDetail),
      updateAlertStatus: vi.fn(), createDecision: vi.fn(),
    };
    render(<MemoryRouter><AlertDetail client={client} alertId="a1" /></MemoryRouter>);
    expect(await screen.findByText(/not proof or cause of fraud/i)).toBeVisible();
    expect(screen.getByText("↑ Higher risk")).toBeVisible();
    expect(screen.getByText("Check device")).toBeVisible();
    expect(screen.getByText("test-v1")).toBeVisible();
  });
});
