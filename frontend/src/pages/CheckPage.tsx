import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Meta } from "../api/types";
import { BikeStep } from "../components/check/BikeStep";
import { EmissionStep } from "../components/check/EmissionStep";
import { SymptomStep } from "../components/check/SymptomStep";
import "../components/check/check.css";
import { BikeFigure } from "../components/scene/BikeFigure";
import { Button } from "../components/ui/Button";
import { Notice } from "../components/ui/Notice";
import { Stepper } from "../components/ui/Stepper";
import { useI18n } from "../i18n/I18nProvider";
import { toNumber, toRequest, useCheck } from "../state/CheckContext";

const LAST_STEP = 3;

/** The three-step check. Answers are kept in CheckContext until a result is saved. */
export function CheckPage({ meta }: { meta: Meta }) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { answers, step, setStep, reset } = useCheck();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const go = (next: number) => { setError(""); setStep(next); window.scrollTo(0, 0); };

  async function submit() {
    const { co, hc } = answers.emission;
    if ((toNumber(co) === null) !== (toNumber(hc) === null)) { setError(t("need_both")); return; }
    setBusy(true);
    setError("");
    try {
      const saved = await api.createDiagnosis(toRequest(answers, meta));
      reset();
      navigate(`/results/${saved.id}`);
    } catch (e) {
      setError(e instanceof ApiError && !e.network ? e.message : t("server"));
      setBusy(false);
    }
  }

  return (
    <div className="container check">
      <div>
        <p className="eyebrow">{t("step", { n: step })}</p>
        <h2 className="check__title">{t("nav_check")}</h2>
        <Stepper step={step} />
        {step === 1 && <BikeStep meta={meta} />}
        {step === 2 && <SymptomStep meta={meta} />}
        {step === 3 && <EmissionStep meta={meta} />}
        {error && <div style={{ marginTop: 14 }}><Notice error>{error}</Notice></div>}
        <div className="check__nav">
          {step > 1 && <Button variant="ghost" onClick={() => go(step - 1)} disabled={busy}>{t("back")}</Button>}
          {step < LAST_STEP
            ? <Button wide onClick={() => go(step + 1)}>{t("next")} <span className="arrow" aria-hidden="true">→</span></Button>
            : <Button wide variant="accent" onClick={submit} disabled={busy}>{t("see")}</Button>}
        </div>
      </div>
      <aside className="check__aside">
        <BikeFigure number={`0${step + 1}`} caption={[t("s1"), t("s2"), t("s3")][step - 1]} turn={step - 1} />
      </aside>
    </div>
  );
}
