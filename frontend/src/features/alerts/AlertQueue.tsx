import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiClient, type AlertFilters, type FraudApi } from "../../api/client";
import type { AlertPage, AlertStatus } from "../../api/schema";

const defaultRange = (): Pick<AlertFilters, "start" | "end"> => ({
  start: new Date(Date.now() - 30 * 86_400_000).toISOString(),
  end: new Date(Date.now() + 86_400_000).toISOString(),
});

export function AlertQueue({ client = apiClient }: { client?: FraudApi }) {
  const [filters, setFilters] = useState<AlertFilters>({ ...defaultRange(), status: "open" });
  const [page, setPage] = useState<AlertPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    void client
      .listAlerts(filters)
      .then(setPage)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unknown error"))
      .finally(() => setLoading(false));
  }, [client, filters]);

  const setStatus = (status: string) => {
    setFilters((current) => ({
      ...current,
      status: status ? (status as AlertStatus) : undefined,
      cursor: undefined,
    }));
  };

  return (
    <main>
      <div className="page-heading">
        <div><span className="eyebrow">Investigation</span><h2>Alert queue</h2></div>
        <div className="filters">
          <label>Status
            <select value={filters.status ?? ""} onChange={(event) => setStatus(event.target.value)}>
              <option value="">All</option><option value="open">Open</option>
              <option value="in_review">In review</option><option value="closed">Closed</option>
            </select>
          </label>
          <label>Minimum risk
            <select value={filters.minRisk ?? ""} onChange={(event) => setFilters((current) => ({ ...current, minRisk: event.target.value ? Number(event.target.value) : undefined, cursor: undefined }))}>
              <option value="">Any</option><option value="0.7">70%+</option><option value="0.9">90%+</option>
            </select>
          </label>
          <label>Channel<input value={filters.channel ?? ""} placeholder="ecommerce" onChange={(event) => setFilters((current) => ({ ...current, channel: event.target.value || undefined, cursor: undefined }))} /></label>
          <label>Country<input value={filters.country ?? ""} placeholder="GB" maxLength={2} onChange={(event) => setFilters((current) => ({ ...current, country: event.target.value.toUpperCase() || undefined, cursor: undefined }))} /></label>
        </div>
      </div>
      {loading && <p role="status">Loading alerts…</p>}
      {error && <div role="alert"><p>Could not load alerts: {error}</p><button onClick={() => setFilters({ ...filters })}>Try again</button></div>}
      {!loading && !error && page?.items.length === 0 && (
        <div className="empty"><h3>No alerts match these filters</h3><button onClick={() => setFilters({ ...defaultRange() })}>Reset filters</button></div>
      )}
      {page && page.items.length > 0 && (
        <div className="queue" aria-label="Risk-prioritized alerts">
          {page.items.map((alert) => (
            <Link className="alert-row" to={`/alerts/${alert.id}`} key={alert.id}>
              <strong>{Math.round(alert.probability * 100)}%</strong>
              <span>{alert.merchantRef ?? "Unknown merchant"}<small>{alert.channel} · {alert.country}</small></span>
              <span>{alert.currency} {alert.amount}</span><span className={`badge ${alert.riskBand}`}>{alert.riskBand}</span>
            </Link>
          ))}
        </div>
      )}
      {page?.nextCursor && <button onClick={() => setFilters((current) => ({ ...current, cursor: page.nextCursor ?? undefined }))}>Next page</button>}
    </main>
  );
}
