import type { EmissionResult, GasCheck, Meta, MlReading } from "../../api/types";
import { formatNumber } from "../../hooks/useFormat";
import { useI18n } from "../../i18n/I18nProvider";
import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";
import "./result.css";

function GasRow({ name, gas, unit }: { name: string; gas: GasCheck; unit: string }) {
  const { t } = useI18n();
  return (
    <div className="row">
      <div><b>{name}</b><div className="small muted">{t("limit")} {formatNumber(gas.limit)} {unit}</div></div>
      <div className="row__value">
        <span>{formatNumber(gas.value)} {unit}</span>
        <Badge tone={gas.pass ? "pass" : "fail"}>{t(gas.pass ? "pass" : "fail")}</Badge>
      </div>
    </div>
  );
}

function ModelReading({ ml, meta }: { ml: MlReading; meta: Meta }) {
  const { t, pick } = useI18n();
  return (
    <div className="ml">
      <div className="eyebrow">{t("ml_h")}</div>
      {ml.status === "ok" && (
        <>
          <p style={{ marginBottom: 4 }}><b>{meta.ml_labels[ml.label] ? pick(meta.ml_labels[ml.label]) : ml.label}</b> · {t("ml_conf", { p: Math.round(ml.confidence * 100) })}</p>
          <p className="small muted" style={{ margin: 0 }}>{t(ml.model === "full" ? "ml_full" : "ml_basic")}</p>
        </>
      )}
      {ml.status === "conflict" && <p className="small" style={{ margin: 0 }}>{t("ml_conflict")}</p>}
      {ml.status === "out_of_range" && <p className="small" style={{ margin: 0 }}>{t("ml_oor", { f: ml.outside.join(", ") })}</p>}
    </div>
  );
}

/** Legal-limit check, plus what the trained model reads from the gas values. */
export function EmissionCard({ emission, meta }: { emission: EmissionResult; meta: Meta }) {
  const { t } = useI18n();
  return (
    <Panel title={t("em_h")}>
      <p className="muted small">{t(emission.pass ? "em_pass" : "em_fail")}</p>
      <GasRow name="CO" gas={emission.co} unit="%" />
      <GasRow name="HC" gas={emission.hc} unit="ppm" />
      {emission.ml && <ModelReading ml={emission.ml} meta={meta} />}
    </Panel>
  );
}
