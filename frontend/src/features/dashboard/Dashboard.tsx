import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiClient, type FraudApi } from "../../api/client";
import type { DashboardSummary } from "../../api/schema";
import { ChartPanel, MetricCard } from "./components";
import { ModelPerformance } from "./ModelPerformance";

function defaultRange() { const end = new Date(); const start = new Date(end.getTime() - 30 * 86_400_000); return { start: start.toISOString(), end: end.toISOString() }; }

export function Dashboard({ client = apiClient }: { client?: FraudApi }) {
  const [range, setRange] = useState(defaultRange);
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { setLoading(true); setError(null); void client.getDashboard(range.start, range.end).then(setData).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unknown error")).finally(() => setLoading(false)); }, [client, range]);
  const empty = data?.totals.transactions === 0;
  return <main><div className="page-heading"><div><span className="eyebrow">Monitoring</span><h2>Operations overview</h2></div><label>Range<select aria-label="Range" onChange={(event) => { const days = Number(event.target.value); const end = new Date(); setRange({ start: new Date(end.getTime() - days * 86_400_000).toISOString(), end: end.toISOString() }); }}><option value="7">Last 7 days</option><option value="30">Last 30 days</option><option value="90">Last 90 days</option></select></label></div>
    {loading && <p role="status">Loading dashboard…</p>}{error && <p role="alert">Could not load dashboard: {error}</p>}
    {data && <><div className="metric-grid"><MetricCard label="Transactions" value={data.totals.transactions} /><MetricCard label="Alerts" value={data.totals.alerts} /><MetricCard label="Amount at risk" value={Number(data.totals.amountAtRisk).toLocaleString(undefined, { minimumFractionDigits: 2 })} hint="Submitted currencies; no FX conversion" /><MetricCard label="Unlabeled alerts" value={data.reviewOutcomes.unlabeled ?? 0} /></div>
      <div className="chart-grid"><ChartPanel title="Volume trend" label="Daily transaction and alert volume" empty={empty}><ResponsiveContainer width="100%" height={260}><BarChart data={data.series}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="bucket" /><YAxis /><Tooltip /><Legend /><Bar dataKey="transactions" fill="#176c58" /><Bar dataKey="alerts" fill="#e08b3e" /></BarChart></ResponsiveContainer></ChartPanel>
      <ChartPanel title="Risk distribution" label="Counts by fraud risk band" empty={empty}><ResponsiveContainer width="100%" height={260}><BarChart data={Object.entries(data.riskBands).map(([band, count]) => ({ band, count }))}><XAxis dataKey="band" /><YAxis /><Tooltip /><Bar dataKey="count" fill="#8d4c7d" /></BarChart></ResponsiveContainer></ChartPanel></div>
      <ChartPanel title="Review outcomes" label="Latest analyst outcomes including unlabeled alerts" empty={data.totals.alerts === 0}><ul>{Object.entries(data.reviewOutcomes).map(([outcome, count]) => <li key={outcome}>{outcome.replaceAll("_", " ")}: {count}</li>)}</ul></ChartPanel></>}
    <ModelPerformance client={client} />
  </main>;
}
