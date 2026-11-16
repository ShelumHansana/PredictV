import type { ReactNode } from "react";
import { useReveal } from "../../hooks/useReveal";
import "./ui.css";

interface Props { title?: string; number?: string; delay?: number; as?: "section" | "article" | "div"; children: ReactNode }

/** A bordered box with an optional numbered heading. Fades in when scrolled to. */
export function Panel({ title, number, delay = 0, as: Tag = "section", children }: Props) {
  const ref = useReveal<HTMLElement>();
  return (
    <Tag ref={ref as never} className="panel reveal" style={{ "--i": delay } as React.CSSProperties}>
      {title && (
        <div className="panel__head">
          {number && <span className="panel__no">{number}</span>}
          <h3>{title}</h3>
        </div>
      )}
      {children}
    </Tag>
  );
}
