import { ButtonLink } from "../components/ui/Button";
import { useI18n } from "../i18n/I18nProvider";

export function NotFoundPage() {
  const { t } = useI18n();
  return (
    <div className="container narrow">
      <p className="eyebrow"><b>404</b></p>
      <h2 style={{ marginBottom: 18 }}>{t("notfound")}</h2>
      <ButtonLink to="/">{t("back_home")}</ButtonLink>
    </div>
  );
}
