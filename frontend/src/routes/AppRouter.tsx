import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { AlertDetail } from "../features/alerts/AlertDetail";
import { AlertQueue } from "../features/alerts/AlertQueue";

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
            <NavLink to="/alerts">Alert queue</NavLink>
          </nav>
        </header>
        <Routes>
          <Route path="*" element={<AlertQueue />} />
          <Route path="/alerts" element={<AlertQueue />} />
          <Route path="/alerts/:alertId" element={<AlertDetail />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
