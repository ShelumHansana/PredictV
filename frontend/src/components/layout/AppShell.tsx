import { useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useI18n } from "../../i18n/I18nProvider";
import { Header } from "./Header";
import "./layout.css";

/** Header, page content and footer. Every page is drawn inside this. */
export function AppShell() {
  const { t } = useI18n();
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return (
    <>
      <Header />
      <main className="main"><Outlet /></main>
      <footer className="footer no-print"><div className="container">{t("footer")}</div></footer>
    </>
  );
}
