// The only place that talks to the backend.
import type { Diagnosis, DiagnoseRequest, DiagnosisSummary, Meta } from "./types";

/** Thrown when the server answered with an error. `network` is true when it could not be reached at all. */
export class ApiError extends Error {
  constructor(message: string, public status: number, public network = false) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      credentials: "same-origin",
      headers: init?.body ? { "Content-Type": "application/json" } : undefined,
      ...init,
    });
  } catch {
    throw new ApiError("network", 0, true);
  }
  if (res.status === 204) return undefined as T;
  // a 5xx without a JSON body means the API is not running behind the dev proxy
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = (body as { detail?: unknown } | null)?.detail;
    const message = typeof detail === "string" ? detail
      : Array.isArray(detail) && detail[0]?.msg ? String(detail[0].msg)
      : res.statusText;
    throw new ApiError(message, res.status, res.status >= 500 && body === null);
  }
  return body as T;
}

export const api = {
  meta: () => request<Meta>("/api/meta"),
  createDiagnosis: (body: DiagnoseRequest) => request<Diagnosis>("/api/diagnoses", { method: "POST", body: JSON.stringify(body) }),
  listDiagnoses: () => request<DiagnosisSummary[]>("/api/diagnoses"),
  getDiagnosis: (id: string) => request<Diagnosis>(`/api/diagnoses/${encodeURIComponent(id)}`),
  deleteDiagnosis: (id: string) => request<void>(`/api/diagnoses/${encodeURIComponent(id)}`, { method: "DELETE" }),
  saveFeedback: (id: string, confirmed_fault: string, note: string) =>
    request<Diagnosis>(`/api/diagnoses/${encodeURIComponent(id)}/feedback`, { method: "PUT", body: JSON.stringify({ confirmed_fault, note: note || null }) }),
};
