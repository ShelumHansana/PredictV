import type { Meta } from "../../api/types";
import { useI18n } from "../../i18n/I18nProvider";
import { useCheck } from "../../state/CheckContext";
import { Field } from "../ui/Field";
import { Panel } from "../ui/Panel";
import { ServiceQuestion } from "./ServiceQuestion";

/** Step 1: which bike, mileage and service history. */
export function BikeStep({ meta }: { meta: Meta }) {
  const { t } = useI18n();
  const { answers, update } = useCheck();
  return (
    <>
      <Panel title={t("s1")} number="1.1">
        <div className="grid-2">
          <Field id="bike-name" label={t("bike_name")} placeholder={t("bike_name_ph")} hint={t("bike_name_hint")} maxLength={80}
            autoComplete="off" value={answers.bikeName} onValue={v => update({ bikeName: v })} />
          <Field id="mileage" label={t("mileage")} hint={t("mileage_hint")} type="number" inputMode="numeric" min={0} max={1000000}
            placeholder="25000" value={answers.mileage} onValue={v => update({ mileage: v })} />
        </div>
      </Panel>
      <Panel title={t("svc_title")} number="1.2" delay={1}>
        <p className="muted small">{t("svc_hint")}</p>
        {meta.service_items.map(item => (
          <ServiceQuestion key={item.id} item={item} value={answers.service[item.id]}
            onChange={state => update({ service: { ...answers.service, [item.id]: state } })} />
        ))}
      </Panel>
    </>
  );
}
