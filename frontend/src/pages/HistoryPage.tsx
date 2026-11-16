import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { DiagnosisSummary, Meta } from "../api/types";
import { Badge } from "../components/ui/Badge";
import { Button, ButtonLink } from "../components/ui/Button";
import { Loading, Notice } from "../components/ui/Notice";
import { useFormatDate } from "../hooks/useFormat";
import { useI18n } from "../i18n/I18nProvider";
import "./pages.css";

/** Every check saved for this browser, newest first. */
export function HistoryPage({ meta }: { meta: Meta }) {
  const { t, lang } = useI18n();
  const formatDate = useFormatDate();
  const [rows, setRows] = useState<DiagnosisSummary[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [confirming, setConfirming] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    setFailed(false);
    api.listDiagnoses().then(r => { if (alive) setRows(r); }).catch(() => { if (alive) setFailed(true); });
    return () => { alive = false; };
  }, [attempt]);

  async function remove(id: string) {
    try {
      await api.deleteDiagnosis(id);
      setRows(current => current?.filter(r => r.id !== id) ?? null);
    } catch {
      setFailed(true);
    } finally {
      setConfirming(null);
    }
  }

  const summary = (row: DiagnosisSummary) => {
    if (!row.top_fault) return t("v_ok");
    const name = meta.faults[row.top_fault]?.[lang] ?? row.top_fault;
    return row.fault_count > 1 ? `${name} · ${t("more_causes", { n: row.fault_count - 1 })}` : name;
  };

  return (
    <div className="container narrow">
      <div className="page-head">
        <h2>{t("history_h")}</h2>
        <p className="muted small">{t("history_note")}</p>
      </div>
      {failed && <Notice error>{t("server")}<div><Button small onClick={() => setAttempt(n => n + 1)}>{t("retry")}</Button></div></Notice>}
      {!failed && rows === null && <Loading label={t("loading")} />}
      {!failed && rows?.length === 0 && (
        <Notice>{t("history_empty")}<div><ButtonLink to="/check" variant="accent" small>{t("home_cta")}</ButtonLink></div></Notice>
      )}
      {!failed && rows && rows.length > 0 && (
        <ul className="history">
          {rows.map(row => (
            <li className="history__item" key={row.id}>
              <span className="history__bar" data-overall={row.overall} aria-hidden="true" />
              <div>
                <div className="history__title">{row.bike_name ?? t("unnamed")}</div>
                <div className="history__sub">
                  <span>{formatDate(row.created_at)}</span>
                  <span>{summary(row)}</span>
                  {row.has_feedback && <Badge tone="pass">{t("confirmed")}</Badge>}
                </div>
              </div>
              <div className="history__actions">
                {confirming === row.id ? (
                  <>
                    <span className="small" style={{ alignSelf: "center" }}>{t("confirm_delete")}</span>
                    <Button variant="danger" small onClick={() => remove(row.id)}>{t("delete")}</Button>
                    <Button variant="ghost" small onClick={() => setConfirming(null)}>{t("cancel")}</Button>
                  </>
                ) : (
                  <>
                    <ButtonLink to={`/results/${row.id}`} small>{t("view")}</ButtonLink>
                    <Button variant="ghost" small onClick={() => setConfirming(row.id)}>{t("delete")}</Button>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
