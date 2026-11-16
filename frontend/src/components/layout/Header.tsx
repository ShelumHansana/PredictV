import { Link, NavLink } from "react-router-dom";
import { useI18n } from "../../i18n/I18nProvider";
import { useTheme } from "../../hooks/useTheme";
import "./layout.css";

export function Header() {
  const { t, lang, setLang } = useI18n();
  const [theme, toggleTheme] = useTheme();
  const other = theme === "dark" ? t("theme_light") : t("theme_dark");
  return (
    <header className="header no-print">
      <div className="container header__row">
        <Link to="/" className="wordmark" aria-label="PredictV"><i aria-hidden="true" />PredictV</Link>
        <nav className="nav" aria-label="Main">
          <NavLink to="/check">{t("nav_check")}</NavLink>
          <NavLink to="/history">{t("nav_history")}</NavLink>
          <NavLink to="/how-it-works">{t("nav_about")}</NavLink>
        </nav>
        <div className="controls">
          <div className="seg" role="group" aria-label={t("language")}>
            <button type="button" aria-pressed={lang === "en"} onClick={() => setLang("en")}>EN</button>
            <button type="button" aria-pressed={lang === "si"} onClick={() => setLang("si")} lang="si">සිං</button>
          </div>
          <button type="button" className="theme-btn" onClick={toggleTheme} aria-label={t("theme_switch", { x: other })}>{other}</button>
        </div>
      </div>
    </header>
  );
}
