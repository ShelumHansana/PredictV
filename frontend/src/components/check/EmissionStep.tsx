import type { Meta } from "../../api/types";
import { formatNumber } from "../../hooks/useFormat";
import { useI18n } from "../../i18n/I18nProvider";
import { useCheck, type EmissionAnswers } from "../../state/CheckContext";
import { Field } from "../ui/Field";
import { Panel } from "../ui/Panel";

/** Step 3 (optional): numbers from an emission test report. */
export function EmissionStep({ meta }: { meta: Meta }) {
  const { t } = useI18n();
  const { answers, update } = useCheck();
  const em = answers.emission;
  const field = (key: keyof EmissionAnswers, placeholder: string, step: string) => (
    <Field id={`em-${key}`} label={t(key)} type="number" inputMode="decimal" min={0} step={step} placeholder={placeholder}
      value={em[key]} onValue={v => update({ emission: { ...em, [key]: v } })} />
  );
  return (
    <Panel title={t("s3")} number="3.1">
      <p className="muted small">{t("s3_intro")}</p>
      <div className="grid-2">{field("co", "2.1", "0.01")}{field("hc", "350", "1")}</div>
      <p className="field__hint">{t("limit")}: CO ≤ {meta.limits.co_percent}% · HC ≤ {formatNumber(meta.limits.hc_ppm)} ppm</p>
      <details className="more" open={Boolean(em.co2 || em.o2 || em.lambda) || undefined}>
        <summary>{t("more")}</summary>
        <div className="grid-2">{field("co2", "13.2", "0.01")}{field("o2", "0.6", "0.01")}{field("lambda", "0.98", "0.001")}</div>
      </details>
    </Panel>
  );
}
