import { BikeFigure } from "../components/scene/BikeFigure";
import { ButtonLink } from "../components/ui/Button";
import { useReveal } from "../hooks/useReveal";
import { useI18n } from "../i18n/I18nProvider";
import "./pages.css";

export function HomePage() {
  const { t } = useI18n();
  const howRef = useReveal<HTMLElement>();
  const steps = [1, 2, 3] as const;
  return (
    <div className="container">
      <section className="hero">
        <div>
          <p className="eyebrow"><b>PV-01</b> · {t("home_eyebrow")}</p>
          <h1>{t("home_title")}</h1>
          <p className="lede">{t("intro")}</p>
          <div className="hero__cta">
            <ButtonLink to="/check" variant="accent">{t("home_cta")} <span className="arrow" aria-hidden="true">→</span></ButtonLink>
            <ButtonLink to="/how-it-works" variant="ghost">{t("nav_about")}</ButtonLink>
          </div>
          <ul className="facts">
            <li>{t("fact1")}</li><li>{t("fact2")}</li><li>{t("fact3")}</li>
          </ul>
        </div>
        <BikeFigure className="hero__figure" number="01" caption="4-stroke single" />
      </section>

      <section className="how reveal" ref={howRef}>
        <h2>{t("how_h")}</h2>
        <div className="how__grid">
          {steps.map(n => (
            <div className="how__item" key={n}>
              <div className="how__no" aria-hidden="true">0{n}</div>
              <h3>{t(`how${n}_t`)}</h3>
              <p>{t(`how${n}_d`)}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
