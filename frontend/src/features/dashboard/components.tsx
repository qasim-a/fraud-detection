import type { ReactNode } from "react";

export function MetricCard({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return <article className="metric-card"><span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</article>;
}

export function ChartPanel({ title, label, children, empty = false }: { title: string; label: string; children: ReactNode; empty?: boolean }) {
  return <section><h3>{title}</h3>{empty ? <p className="empty-chart">No observed data for this range.</p> : <div role="img" aria-label={label} className="chart">{children}</div>}</section>;
}
