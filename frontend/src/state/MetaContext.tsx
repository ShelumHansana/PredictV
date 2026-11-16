import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { Meta } from "../api/types";

interface MetaState { meta: Meta | null; failed: boolean; reload: () => void }
const Ctx = createContext<MetaState | null>(null);

/** Loads the questions and fault texts once and shares them with every page. */
export function MetaProvider({ children }: { children: ReactNode }) {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    setFailed(false);
    api.meta().then(m => { if (alive) setMeta(m); }).catch(() => { if (alive) setFailed(true); });
    return () => { alive = false; };
  }, [attempt]);

  const reload = useCallback(() => setAttempt(n => n + 1), []);
  return <Ctx.Provider value={{ meta, failed, reload }}>{children}</Ctx.Provider>;
}

export function useMeta(): MetaState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useMeta must be used inside <MetaProvider>");
  return ctx;
}
