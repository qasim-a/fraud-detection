import { lazy, Suspense } from "react";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { AlertDetail } from "../features/alerts/AlertDetail";
import { AlertQueue } from "../features/alerts/AlertQueue";

const Dashboard = lazy(() =>
  import("../features/dashboard/Dashboard").then((module) => ({ default: module.Dashboard })),
);

export function AppRouter() {
  return (
    <BrowserRouter>
      <div className="shell">
        <header>
          <div>
            <span className="eyebrow">Risk operations</span>
            <h1>Fraud Review Platform</h1>
          </div>
          <nav aria-label="Primary navigation">
            <NavLink to="/">Dashboard</NavLink>
            <NavLink to="/alerts">Alert queue</NavLink>
          </nav>
        </header>
        <Suspense fallback={<main><p role="status">Loading workspace…</p></main>}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="*" element={<Dashboard />} />
            <Route path="/alerts" element={<AlertQueue />} />
            <Route path="/alerts/:alertId" element={<AlertDetail />} />
          </Routes>
        </Suspense>
      </div>
    </BrowserRouter>
  );
}
