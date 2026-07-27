import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiClient, type FraudApi } from "../../api/client";
import type { AlertDetail as AlertDetailType } from "../../api/schema";
import { ReviewControls } from "./ReviewControls";

export function AlertDetail({ client = apiClient, alertId: suppliedId }: { client?: FraudApi; alertId?: string }) {
  const route = useParams();
  const alertId = suppliedId ?? route.alertId ?? "";
  const [alert, setAlert] = useState<AlertDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const reload = () => void client.getAlert(alertId).then(setAlert).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unknown error"));
  useEffect(reload, [alertId, client]);

  if (error) return <main><p role="alert">Could not load alert: {error}</p></main>;
  if (!alert) return <main><p role="status">Loading alert…</p></main>;
  return <main>
    <Link to="/alerts">← Back to queue</Link>
    <div className="detail-heading"><div><span className="eyebrow">{alert.status.replace("_", " ")}</span><h2>{alert.merchantRef}</h2></div><strong className="score">{Math.round(alert.probability * 100)}%</strong></div>
    <section><h3>Transaction context</h3><dl><div><dt>Amount</dt><dd>{alert.currency} {alert.amount}</dd></div><div><dt>Channel</dt><dd>{alert.channel}</dd></div><div><dt>Country</dt><dd>{alert.country}</dd></div><div><dt>Model</dt><dd>{alert.score.modelVersion}</dd></div></dl></section>
    <section><h3>Score factors</h3><p className="disclaimer">{alert.explanationDisclaimer}</p><ol>{alert.score.factors.map((factor) => <li key={factor.feature}><strong>{factor.label}</strong><span>{factor.direction === "higher" ? "↑ Higher risk" : "↓ Lower risk"}</span></li>)}</ol></section>
    <ReviewControls alert={alert} client={client} onUpdated={reload} />
    <section><h3>Audit history</h3>{alert.history.length === 0 ? <p>No history yet.</p> : <ol>{alert.history.map((event) => <li key={event.id}>{event.eventType.replaceAll("_", " ")} · {event.actorRef}</li>)}</ol>}{(alert.decisions ?? []).map((decision) => <article key={decision.id}><strong>{decision.outcome.replaceAll("_", " ")}</strong><p>{decision.note ?? "No note"}</p><small>{decision.reviewerRef}</small></article>)}</section>
  </main>;
}
