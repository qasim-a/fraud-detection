import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "..",
  testMatch: ["tests/e2e/*.spec.ts", "frontend/tests/*.spec.ts"],
  fullyParallel: false,
  use: { baseURL: "http://127.0.0.1:5173", trace: "retain-on-failure" },
  webServer: {
    command: "pnpm run dev",
    cwd: import.meta.dirname,
    url: "http://127.0.0.1:5173",
    reuseExistingServer: true,
  },
});
