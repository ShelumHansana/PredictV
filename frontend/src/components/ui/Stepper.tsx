import { useI18n } from "../../i18n/I18nProvider";
import "./ui.css";

/** The three numbered tabs above the wizard. */
export function Stepper({ step }: { step: number }) {
  const { t } = useI18n();
  const names = [t("s1"), t("s2"), t("s3")];
  return (
    <ol className="stepper" aria-label={t("step", { n: step })}>
      {names.map((name, i) => {
        const n = i + 1;
        return (
          <li key={n} data-state={n < step ? "done" : n === step ? "current" : "todo"} aria-current={n === step ? "step" : undefined}>
            <span>0{n}</span><span className="stepper__name">{name}</span>
          </li>
        );
      })}
    </ol>
  );
}
