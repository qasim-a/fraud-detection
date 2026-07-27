/** Hand-maintained public API types mirrored from contracts/openapi.yaml. */

export type ServiceAvailability = "available" | "unavailable";

export interface Health {
  status: "ok" | "degraded";
  database: ServiceAvailability;
  model: ServiceAvailability;
}

export type TransactionChannel = "card_present" | "ecommerce" | "wallet" | "atm";
export type RiskBand = "low" | "medium" | "high" | "critical";
export type AlertStatus = "open" | "in_review" | "closed";
export type ReviewOutcome = "confirmed_fraud" | "legitimate" | "needs_review";

export interface TransactionInput {
  id: string;
  eventTime: string;
  accountId: string;
  merchantId: string;
  amount: string;
  currency: string;
  channel: TransactionChannel;
  country: string;
  region: string;
  deviceId: string;
  ipHash: string;
}

export interface ExplanationFactor {
  feature: string;
  label: string;
  direction: "higher" | "lower";
  contribution: number;
}

export interface FraudScore {
  id: string;
  probability: number;
  riskBand: RiskBand;
  threshold: number;
  modelVersion: string;
  featureVersion: string;
  scoredAt: string;
  explanationStatus: "available" | "unavailable";
  factors: ExplanationFactor[];
}

export interface TransactionResult {
  transactionId: string;
  status: "scored" | "scoring_failed";
  ingestedAt: string;
  score?: FraudScore;
  alertId?: string | null;
  failureCode?: string | null;
}

export interface AlertSummary {
  id: string;
  transactionId: string;
  probability: number;
  riskBand: RiskBand;
  amount: string;
  currency: string;
  merchantRef?: string;
  channel?: string;
  country?: string;
  status: AlertStatus;
  createdAt: string;
}

export interface AlertPage {
  items: AlertSummary[];
  nextCursor?: string | null;
}

export interface ReviewDecisionInput {
  outcome: ReviewOutcome;
  note?: string | null;
}

export interface ReviewDecision extends ReviewDecisionInput {
  id: string;
  alertId: string;
  reviewerRef: string;
  createdAt: string;
}

export interface HistoryEvent {
  id: string;
  eventType: "created" | "status_changed" | "decision_recorded" | "reopened";
  fromStatus?: AlertStatus | null;
  toStatus?: AlertStatus | null;
  actorRef: string;
  createdAt: string;
}

export interface AlertDetail extends AlertSummary {
  transaction: TransactionInput;
  score: FraudScore;
  history: HistoryEvent[];
  decisions?: ReviewDecision[];
  explanationDisclaimer: string;
}

export interface DashboardSummary {
  range: { start: string; end: string };
  totals: { transactions: number; alerts: number; amountAtRisk: string };
  riskBands: Record<string, number>;
  reviewOutcomes: Record<string, number>;
  series: Array<{ bucket: string; transactions: number; alerts: number }>;
}

export interface ModelMetrics {
  precision: number;
  recall: number;
  prAuc: number;
  truePositive: number;
  falsePositive: number;
  trueNegative: number;
  falseNegative: number;
  alertVolume: number;
}

export interface ModelSummary {
  version: string;
  featureVersion: string;
  datasetId: string;
  threshold: number;
  metrics: ModelMetrics;
  activatedAt: string;
}

export interface Problem {
  type: string;
  title: string;
  status: number;
  detail: string;
  errors?: Array<{ field: string; message: string }>;
}
