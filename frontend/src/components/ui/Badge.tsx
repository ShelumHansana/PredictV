import type { ReactNode } from "react";
import "./ui.css";

export function Badge({ tone, children }: { tone?: "pass" | "warn" | "fail"; children: ReactNode }) {
  return <span className={tone ? `badge badge--${tone}` : "badge"}>{children}</span>;
}
