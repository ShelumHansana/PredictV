import type { ReactElement } from "react";
import { Route, Routes } from "react-router-dom";
import type { Meta } from "./api/types";
import { AppShell } from "./components/layout/AppShell";
import { Button } from "./components/ui/Button";
import { Loading, Notice } from "./components/ui/Notice";
import { useI18n } from "./i18n/I18nProvider";
import { AboutPage } from "./pages/AboutPage";
import { CheckPage } from "./pages/CheckPage";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { ResultPage } from "./pages/ResultPage";
import { useMeta } from "./state/MetaContext";

/** Pages that need the questions and fault texts wait here until they have loaded. */
function WithMeta({ render }: { render: (meta: Meta) => ReactElement }) {
  const { meta, failed, reload } = useMeta();
  const { t } = useI18n();
  if (meta) return render(meta);
  return (
    <div className="container narrow">
      {failed
        ? <Notice error>{t("server")}<div><Button small onClick={reload}>{t("retry")}</Button></div></Notice>
        : <Loading label={t("loading")} />}
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="check" element={<WithMeta render={meta => <CheckPage meta={meta} />} />} />
        <Route path="results/:id" element={<WithMeta render={meta => <ResultPage meta={meta} />} />} />
        <Route path="history" element={<WithMeta render={meta => <HistoryPage meta={meta} />} />} />
        <Route path="how-it-works" element={<WithMeta render={meta => <AboutPage meta={meta} />} />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
