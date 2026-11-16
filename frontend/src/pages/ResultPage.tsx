import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Diagnosis, Meta } from "../api/types";
import { EmissionCard } from "../components/result/EmissionCard";
import { FaultCard } from "../components/result/FaultCard";
import { FeedbackForm } from "../components/result/FeedbackForm";
import "../components/result/result.css";
import { ServiceStatus } from "../components/result/ServiceStatus";
import { Verdict } from "../components/result/Verdict";
import { Button, ButtonLink } from "../components/ui/Button";
import { Loading, Notice } from "../components/ui/Notice";
import { useFormatDate } from "../hooks/useFormat";
import { useI18n } from "../i18n/I18nProvider";

type State = { status: "loading" } | { status: "missing" } | { status: "error" } | { status: "ready"; diagnosis: Diagnosis };

/** One saved check, loaded by its id from the address bar. */
export function ResultPage({ meta }: { meta: Meta }) {
  const { id = "" } = useParams();
  const { t } = useI18n();
  const formatDate = useFormatDate();
  const [state, setState] = useState<State>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    setState({ status: "loading" });
    api.getDiagnosis(id)
      .then(diagnosis => { if (alive) setState({ status: "ready", diagnosis }); })
      .catch((e: unknown) => { if (alive) setState({ status: e instanceof ApiError && e.status === 404 ? "missing" : "error" }); });
    return () => { alive = false; };
  }, [id, attempt]);

  if (state.status === "loading") return <div className="container narrow"><Loading label={t("loading")} /></div>;
  if (state.status === "missing") return (
    <div className="container narrow"><Notice>{t("result_missing")}<div><ButtonLink to="/check" small>{t("new_check")}</ButtonLink></div></Notice></div>
  );
  if (state.status === "error") return (
    <div className="container narrow"><Notice error>{t("server")}<div><Button small onClick={() => setAttempt(n => n + 1)}>{t("retry")}</Button></div></Notice></div>
  );

  const { diagnosis } = state;
  const { result } = diagnosis;
  return (
    <div className="container narrow">
      <div className="result__meta">
        <span className="eyebrow"><b>{diagnosis.bike_name ?? t("unnamed")}</b></span>
        <span className="eyebrow">{t("saved_on", { d: formatDate(diagnosis.created_at) })}</span>
      </div>
      <Verdict overall={result.overall} />

      {result.faults.length > 0 && (
        <>
          <h2 className="result__section">{t("faults_h")}</h2>
          {result.faults.map((fault, i) => <FaultCard key={fault.id} fault={fault} index={i} meta={meta} />)}
        </>
      )}

      <div className="result__section">
        {result.emission && <EmissionCard emission={result.emission} meta={meta} />}
        <ServiceStatus service={result.service} meta={meta} />
        <FeedbackForm diagnosis={diagnosis} meta={meta} onSaved={d => setState({ status: "ready", diagnosis: d })} />
      </div>

      <p className="small muted">{t("disclaimer")}</p>
      <div className="result__actions no-print">
        <ButtonLink to="/check" variant="accent">{t("new_check")}</ButtonLink>
        <Button variant="ghost" onClick={() => window.print()}>{t("print")}</Button>
        <ButtonLink to="/history" variant="ghost">{t("nav_history")}</ButtonLink>
      </div>
    </div>
  );
}
