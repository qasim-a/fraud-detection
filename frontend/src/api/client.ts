import type {
  AlertDetail,
  AlertPage,
  AlertStatus,
  AlertSummary,
  DashboardSummary,
  ModelSummary,
  Problem,
  ReviewDecision,
  ReviewDecisionInput,
} from "./schema";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly problem: Problem,
  ) {
    super(problem.detail);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = (await response.json()) as Problem;
    throw new ApiError(response.status, body);
  }
  return (await response.json()) as T;
}

export interface AlertFilters {
  start: string;
  end: string;
  status?: AlertStatus;
  minRisk?: number;
  merchant?: string;
  channel?: string;
  country?: string;
  limit?: number;
  cursor?: string;
}

export interface FraudApi {
  listAlerts(filters: AlertFilters): Promise<AlertPage>;
  getAlert(id: string): Promise<AlertDetail>;
  updateAlertStatus(id: string, status: AlertStatus): Promise<AlertSummary>;
  createDecision(id: string, input: ReviewDecisionInput): Promise<ReviewDecision>;
  getDashboard(start: string, end: string): Promise<DashboardSummary>;
  getActiveModel(): Promise<ModelSummary>;
}

export const apiClient: FraudApi = {
  listAlerts(filters) {
    const parameters = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== "") parameters.set(key, String(value));
    });
    return request<AlertPage>(`/alerts?${parameters.toString()}`);
  },
  getAlert: (id) => request<AlertDetail>(`/alerts/${id}`),
  updateAlertStatus: (id, status) =>
    request<AlertSummary>(`/alerts/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  createDecision: (id, input) =>
    request<ReviewDecision>(`/alerts/${id}/decisions`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  getDashboard: (start, end) => {
    const parameters = new URLSearchParams({ start, end });
    return request<DashboardSummary>(`/dashboard/summary?${parameters.toString()}`);
  },
  getActiveModel: () => request<ModelSummary>("/models/active"),
};
