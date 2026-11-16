import type { FaultResult, Meta } from "../../api/types";
import { useI18n } from "../../i18n/I18nProvider";
import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";
import "./result.css";

/** Turns an evidence key from the API into a sentence. */
function useReasonText(meta: Meta) {
  const { t, pick } = useI18n();
  return (key: string): string => {
    if (key.startsWith("svc:")) {
      const [, id, state] = key.split(":");
      const item = meta.service_items.find(i => i.id === id);
      return t(state === "overdue" ? "r_overdue" : "r_due", { x: item ? pick(item) : id });
    }
    if (key.startsWith("ml:")) { const label = meta.ml_labels[key.slice(3)]; return t("r_ml", { x: label ? pick(label) : key }); }
    if (key === "gas:co_high") return t("r_co");
    if (key === "gas:hc_high") return t("r_hc");
    if (key === "high_mileage") return t("r_mileage");
    for (const group of meta.symptom_groups) {
      const symptom = group.symptoms.find(s => s.id === key);
      if (symptom) return pick(symptom);
    }
    return key;
  };
}

interface Props { fault: FaultResult; index: number; meta: Meta }

/** One probable fault: what it is, what to do about it, and why it was picked. */
export function FaultCard({ fault, index, meta }: Props) {
  const { t, lang } = useI18n();
  const reason = useReasonText(meta);
  const info = meta.faults[fault.id];
  if (!info) return null;
  const urgencyTone = fault.urgency === "high" ? "fail" : fault.urgency === "medium" ? "warn" : undefined;
  return (
    <Panel as="article" delay={Math.min(index, 3)}>
      <div className="fault">
        <div className="fault__head">
          <span className="fault__no" aria-hidden="true">{index + 1}</span>
          <div>
            <h3>{lang === "si" ? info.si : info.en}</h3>
            <div className="fault__badges">
              <Badge tone={fault.level === "likely" ? "fail" : "warn"}>{t(fault.level)}</Badge>
              <Badge tone={urgencyTone}>{t(`u_${fault.urgency}`)}</Badge>
              <Badge>{t(fault.who)}</Badge>
            </div>
          </div>
        </div>
        <p>{lang === "si" ? info.what_si : info.what_en}</p>
        <div className="fault__cols">
          <div>
            <div className="eyebrow">{t("fix")}</div>
            <ol>{(lang === "si" ? info.fix_si : info.fix_en).map(step => <li key={step}>{step}</li>)}</ol>
          </div>
          <div>
            <div className="eyebrow">{t("why")}</div>
            <ul>{fault.reasons.map(r => <li key={r}>{reason(r)}</li>)}</ul>
          </div>
        </div>
      </div>
    </Panel>
  );
}
