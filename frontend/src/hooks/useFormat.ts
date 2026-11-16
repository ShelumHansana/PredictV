import { useI18n } from "../i18n/I18nProvider";

export const formatNumber = (n: number) => n.toLocaleString("en-US");

/** Date formatting that follows the chosen language. */
export function useFormatDate() {
  const { lang } = useI18n();
  return (iso: string) => new Date(iso).toLocaleDateString(lang === "si" ? "si-LK" : "en-GB", { day: "numeric", month: "short", year: "numeric" });
}
