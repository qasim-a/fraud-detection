import { useState } from "react";
import type { FraudApi } from "../../api/client";
import type { AlertDetail, AlertStatus, ReviewOutcome } from "../../api/schema";

export function ReviewControls({ alert, client, onUpdated }: { alert: AlertDetail; client: FraudApi; onUpdated: () => void }) {
  const [outcome, setOutcome] = useState<ReviewOutcome>("needs_review");
  const [note, setNote] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = async (action: () => Promise<unknown>) => {
    setPending(true); setError(null);
    try { await action(); onUpdated(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Update failed"); } finally { setPending(false); }
  };
  return <section><h3>Review controls</h3>
    <label>Status<select value={alert.status} disabled={pending} onChange={(event) => void run(() => client.updateAlertStatus(alert.id, event.target.value as AlertStatus))}><option value="open">Open</option><option value="in_review">In review</option><option value="closed">Closed</option></select></label>
    <label>Decision<select value={outcome} onChange={(event) => setOutcome(event.target.value as ReviewOutcome)}><option value="needs_review">Needs review</option><option value="confirmed_fraud">Confirmed fraud</option><option value="legitimate">Legitimate</option></select></label>
    <label>Optional note<textarea maxLength={2000} value={note} onChange={(event) => setNote(event.target.value)} /></label>
    <button disabled={pending} onClick={() => void run(() => client.createDecision(alert.id, { outcome, note: note || null }))}>{pending ? "Saving…" : "Record decision"}</button>
    {error && <p role="alert">{error}</p>}
  </section>;
}
