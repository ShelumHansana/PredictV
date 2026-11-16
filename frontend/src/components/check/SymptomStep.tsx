import type { Meta } from "../../api/types";
import { useI18n } from "../../i18n/I18nProvider";
import { useCheck } from "../../state/CheckContext";
import { Panel } from "../ui/Panel";

/** Step 2: tick the symptoms. */
export function SymptomStep({ meta }: { meta: Meta }) {
  const { t, pick } = useI18n();
  const { answers, toggleSymptom } = useCheck();
  return (
    <Panel title={t("s2")} number="2.1">
      <p className="muted small">{t("s2_hint")}</p>
      {meta.symptom_groups.map(group => (
        <fieldset key={group.id} className="group" style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}>
          <legend className="eyebrow group__title">{pick(group)}</legend>
          {group.symptoms.map(symptom => (
            <label key={symptom.id} className="tick">
              <input type="checkbox" checked={answers.symptoms.includes(symptom.id)} onChange={() => toggleSymptom(symptom.id)} />
              <span>{pick(symptom)}</span>
            </label>
          ))}
        </fieldset>
      ))}
    </Panel>
  );
}
