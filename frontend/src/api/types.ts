// Shapes returned by the API (see backend/app/schemas.py and routers/meta.py).

export interface Bilingual { en: string; si: string }

export interface Symptom extends Bilingual { id: string }
export interface SymptomGroup extends Bilingual { id: string; symptoms: Symptom[] }
export interface ServiceItem extends Bilingual { id: ServiceId; limits_km: [number, number] }
export type ServiceId = "oil" | "air_filter" | "spark_plug";
export type ServiceState = "recent" | "due" | "overdue" | "unknown";

export interface FaultInfo extends Bilingual {
  what_en: string; what_si: string;
  fix_en: string[]; fix_si: string[];
  who: "diy" | "mechanic";
  urgency: "low" | "medium" | "high";
}

export interface ModelInfo {
  features: string[];
  holdout_accuracy: number;
  blocked_cv_accuracy_mean: number;
  blocked_cv_accuracy_std: number;
  training_range: Record<string, [number, number]>;
}

export interface Meta {
  symptom_groups: SymptomGroup[];
  service_items: ServiceItem[];
  faults: Record<string, FaultInfo>;
  limits: { co_percent: number; hc_ppm: number };
  ml_labels: Record<string, Bilingual>;
  ml: {
    ready: boolean;
    trained_on: string | null;
    dataset: { name: string; rows_raw: number; rows_used: number } | null;
    models: Record<string, ModelInfo>;
    symptom_model: { trained_on: string; rows: number; cv_accuracy: number; classes: string[] } | null;
  };
}

export interface FaultResult {
  id: string;
  score: number;
  level: "likely" | "possible";
  reasons: string[];
  who: "diy" | "mechanic";
  urgency: "low" | "medium" | "high";
  learned_probability?: number;
}

export interface GasCheck { value: number; limit: number; pass: boolean }

export type MlReading =
  | { status: "ok"; model: "full" | "basic"; label: string; confidence: number }
  | { status: "conflict"; model: "full" | "basic" }
  | { status: "out_of_range"; model: "full" | "basic"; outside: string[] };

export interface EmissionResult { co: GasCheck; hc: GasCheck; pass: boolean; ml: MlReading | null }

export type Overall = "ok" | "attention" | "fix_now";

export interface DiagnosisResult {
  overall: Overall;
  faults: FaultResult[];
  service: Record<ServiceId, ServiceState>;
  emission: EmissionResult | null;
  learned_model_used: boolean;
}

export interface Feedback { confirmed_fault: string; note: string | null; created_at: string }

export interface Diagnosis {
  id: string;
  created_at: string;
  bike_name: string | null;
  overall: Overall;
  result: DiagnosisResult;
  feedback: Feedback | null;
}

export interface DiagnosisSummary {
  id: string;
  created_at: string;
  bike_name: string | null;
  overall: Overall;
  top_fault: string | null;
  fault_count: number;
  has_feedback: boolean;
}

export interface DiagnoseRequest {
  bike: { name: string | null; mileage_km: number | null };
  symptoms: string[];
  service: Record<ServiceId, number | null>;
  emission: {
    co_percent: number | null; hc_ppm: number | null; co2_percent: number | null;
    o2_percent: number | null; lambda_value: number | null;
  };
}
