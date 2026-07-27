import { useEffect, useState } from "react";
import { apiClient, type FraudApi } from "../../api/client";
import type { ModelSummary } from "../../api/schema";
import { MetricCard } from "./components";

export function ModelPerformance({ client = apiClient }: { client?: FraudApi }) {
  const [model, setModel] = useState<ModelSummary | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => { void client.getActiveModel().then(setModel).catch(() => setUnavailable(true)); }, [client]);
  if (unavailable) return <section><h3>Model performance</h3><p>Evaluation unavailable—no complete labeled evaluation is registered.</p></section>;
  if (!model) return <section><h3>Model performance</h3><p role="status">Loading model evaluation…</p></section>;
  const metrics = model.metrics;
  return <section><div className="section-heading"><div><h3>Model performance</h3><p>{model.version} · dataset {model.datasetId}</p></div><span>Threshold {Math.round(model.threshold * 100)}%</span></div>
    <div className="metric-grid"><MetricCard label="Precision" value={`${Math.round(metrics.precision * 100)}%`} /><MetricCard label="Recall" value={`${Math.round(metrics.recall * 100)}%`} /><MetricCard label="PR-AUC" value={metrics.prAuc.toFixed(3)} /><MetricCard label="Alert volume" value={metrics.alertVolume} /></div>
    <table><caption>Evaluation confusion counts</caption><thead><tr><th>True positive</th><th>False positive</th><th>True negative</th><th>False negative</th></tr></thead><tbody><tr><td>{metrics.truePositive}</td><td>{metrics.falsePositive}</td><td>{metrics.trueNegative}</td><td>{metrics.falseNegative}</td></tr></tbody></table>
  </section>;
}
