import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("setup screen", () => {
  it("names the platform and settles the lazy dashboard route", async () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Fraud Review Platform" })).toBeVisible();
    expect(await screen.findByRole("heading", { name: "Operations overview" })).toBeVisible();
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load dashboard");
    expect(await screen.findByText(/no complete labeled evaluation/i)).toBeVisible();
  });
});
