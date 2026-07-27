import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("setup screen", () => {
  it("names the platform", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Fraud Review Platform" })).toBeVisible();
  });
});
