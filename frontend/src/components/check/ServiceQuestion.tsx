import type { ServiceItem, ServiceState } from "../../api/types";
import { formatNumber } from "../../hooks/useFormat";
import { useI18n } from "../../i18n/I18nProvider";

interface Props { item: ServiceItem; value: ServiceState | undefined; onChange: (value: ServiceState) => void }

/** "When was this last done?" with four answers. */
export function ServiceQuestion({ item, value, onChange }: Props) {
  const { t, pick } = useI18n();
  const [a, b] = item.limits_km;
  const options: [ServiceState, string][] = [
    ["recent", t("under", { a: formatNumber(a) })],
    ["due", t("between", { a: formatNumber(a), b: formatNumber(b) })],
    ["overdue", t("over", { b: formatNumber(b) })],
    ["unknown", t("unknown")],
  ];
  return (
    <div className="service">
      <span className="service__name" id={`svc-${item.id}`}>{pick(item)}</span>
      <div className="chips" role="group" aria-labelledby={`svc-${item.id}`}>
        {options.map(([state, label]) => (
          <button key={state} type="button" className="chip" aria-pressed={value === state} onClick={() => onChange(state)}>{label}</button>
        ))}
      </div>
    </div>
  );
}
