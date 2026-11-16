import type { ReactNode } from "react";
import "./ui.css";

export function Notice({ error, children }: { error?: boolean; children: ReactNode }) {
  return <div className={error ? "notice notice--error" : "notice"} role={error ? "alert" : "status"}>{children}</div>;
}

export function Loading({ label }: { label: string }) {
  return <p className="muted" role="status"><span className="spinner" aria-hidden="true" />{label}</p>;
}
