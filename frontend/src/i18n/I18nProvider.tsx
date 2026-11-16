import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { strings, type Lang } from "./strings";

type Vars = Record<string, string | number>;
interface I18n {
  lang: Lang;
  setLang: (lang: Lang) => void;
  /** Translate a key, filling {placeholders}. */
  t: (key: string, vars?: Vars) => string;
  /** Pick the current language from an object that has `en` and `si`. */
  pick: (obj: { en: string; si: string }) => string;
}

const Ctx = createContext<I18n | null>(null);
const STORAGE_KEY = "predictv_lang";

function initialLang(): Lang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "en" || saved === "si") return saved;
  } catch { /* storage blocked */ }
  return "en";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang);

  useEffect(() => { document.documentElement.lang = lang; }, [lang]);

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try { localStorage.setItem(STORAGE_KEY, next); } catch { /* storage blocked */ }
  }, []);

  const value = useMemo<I18n>(() => ({
    lang,
    setLang,
    t: (key, vars = {}) => (strings[lang][key] ?? strings.en[key] ?? key).replace(/\{(\w+)\}/g, (_, name: string) => String(vars[name] ?? "")),
    pick: obj => obj[lang] ?? obj.en,
  }), [lang, setLang]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useI18n(): I18n {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useI18n must be used inside <I18nProvider>");
  return ctx;
}
