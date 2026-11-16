import type { Overall } from "../../api/types";
import { useReveal } from "../../hooks/useReveal";
import { useI18n } from "../../i18n/I18nProvider";
import "./result.css";

/** The coloured summary at the top of a result. */
export function Verdict({ overall }: { overall: Overall }) {
  const { t } = useI18n();
  const ref = useReveal<HTMLDivElement>();
  return (
    <div ref={ref} className={`verdict verdict--${overall} reveal`} role="status">
      <h2>{t(`v_${overall}`)}</h2>
      <p>{t(`v_${overall}_d`)}</p>
    </div>
  );
}
