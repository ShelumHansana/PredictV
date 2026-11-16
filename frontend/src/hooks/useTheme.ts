import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark";

const current = (): Theme => (document.documentElement.dataset.theme === "dark" ? "dark" : "light");

/** Light/dark theme. The first value is set in index.html before the page paints. */
export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(current);

  useEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);

  const toggle = useCallback(() => setTheme(t => {
    const next = t === "dark" ? "light" : "dark";
    try { localStorage.setItem("predictv_theme", next); } catch { /* storage blocked */ }
    return next;
  }), []);

  return [theme, toggle];
}
