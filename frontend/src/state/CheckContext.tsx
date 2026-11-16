import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { DiagnoseRequest, Meta, ServiceId, ServiceState } from "../api/types";

export interface EmissionAnswers { co: string; hc: string; co2: string; o2: string; lambda: string }
export interface Answers {
  bikeName: string;
  mileage: string;
  service: Partial<Record<ServiceId, ServiceState>>;
  symptoms: string[];
  emission: EmissionAnswers;
}

const empty: Answers = {
  bikeName: "", mileage: "", service: {}, symptoms: [],
  emission: { co: "", hc: "", co2: "", o2: "", lambda: "" },
};

interface CheckState {
  answers: Answers;
  step: number;
  setStep: (step: number) => void;
  update: (patch: Partial<Answers>) => void;
  toggleSymptom: (id: string) => void;
  reset: () => void;
}
const Ctx = createContext<CheckState | null>(null);

/** Holds the wizard answers so they survive moving between pages. */
export function CheckProvider({ children }: { children: ReactNode }) {
  const [answers, setAnswers] = useState<Answers>(empty);
  const [step, setStep] = useState(1);

  const update = useCallback((patch: Partial<Answers>) => setAnswers(a => ({ ...a, ...patch })), []);
  const toggleSymptom = useCallback((id: string) => setAnswers(a => ({
    ...a, symptoms: a.symptoms.includes(id) ? a.symptoms.filter(s => s !== id) : [...a.symptoms, id],
  })), []);
  const reset = useCallback(() => { setAnswers(empty); setStep(1); }, []);

  const value = useMemo(() => ({ answers, step, setStep, update, toggleSymptom, reset }), [answers, step, update, toggleSymptom, reset]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useCheck(): CheckState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useCheck must be used inside <CheckProvider>");
  return ctx;
}

export const toNumber = (s: string): number | null => (s.trim() === "" || Number.isNaN(Number(s)) ? null : Number(s));

/** The rider picks a range; the API wants kilometres. */
function kmFor(limits: [number, number], choice: ServiceState | undefined): number | null {
  const [ok, overdue] = limits;
  if (choice === "recent") return ok / 2;
  if (choice === "due") return (ok + overdue) / 2;
  if (choice === "overdue") return overdue + 1;
  return null;
}

export function toRequest(a: Answers, meta: Meta): DiagnoseRequest {
  const service = { oil: null, air_filter: null, spark_plug: null } as Record<ServiceId, number | null>;
  for (const item of meta.service_items) service[item.id] = kmFor(item.limits_km, a.service[item.id]);
  return {
    bike: { name: a.bikeName.trim() || null, mileage_km: toNumber(a.mileage) },
    symptoms: a.symptoms,
    service,
    emission: {
      co_percent: toNumber(a.emission.co), hc_ppm: toNumber(a.emission.hc), co2_percent: toNumber(a.emission.co2),
      o2_percent: toNumber(a.emission.o2), lambda_value: toNumber(a.emission.lambda),
    },
  };
}
