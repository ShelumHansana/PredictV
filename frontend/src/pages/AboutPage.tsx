import type { Meta } from "../api/types";
import { ButtonLink } from "../components/ui/Button";
import { formatNumber } from "../hooks/useFormat";
import { useI18n } from "../i18n/I18nProvider";
import "./pages.css";

const percent = (x: number | undefined) => (x === undefined ? "–" : (x * 100).toFixed(1));

/** Plain-language explanation of how results are produced, with the model's real numbers. */
export function AboutPage({ meta }: { meta: Meta }) {
  const { t } = useI18n();
  const { ml, limits } = meta;
  return (
    <div className="container narrow about">
      <p className="eyebrow"><b>PV-02</b> · {t("nav_about")}</p>
      <h2>{t("about_h")}</h2>

      <section>
        <h3>{t("about_rules_h")}</h3>
        <p>{t("about_rules_p", { n: Object.keys(meta.faults).length })}</p>
      </section>
      <section>
        <h3>{t("about_em_h")}</h3>
        <p>{t("about_em_p", { co: limits.co_percent, hc: formatNumber(limits.hc_ppm) })}</p>
      </section>
      <section>
        <h3>{t("about_ml_h")}</h3>
        <p>{t("about_ml_p", { rows: formatNumber(ml.dataset?.rows_used ?? 0) })}</p>
        {ml.ready && (
          <p className="stat">{t("about_ml_acc", { full: percent(ml.models.full?.blocked_cv_accuracy_mean), basic: percent(ml.models.basic?.blocked_cv_accuracy_mean) })}</p>
        )}
      </section>
      <section>
        <h3>{t("about_learn_h")}</h3>
        <p>{t("about_learn_p")}</p>
        <p className="stat">{ml.symptom_model ? t("about_learn_on", { n: ml.symptom_model.rows }) : t("about_learn_off")}</p>
      </section>
      <section>
        <h3>{t("about_limits_h")}</h3>
        <p>{t("disclaimer")}</p>
        <ButtonLink to="/check" variant="accent">{t("home_cta")}</ButtonLink>
      </section>
    </div>
  );
}
