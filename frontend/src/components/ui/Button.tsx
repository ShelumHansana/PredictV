import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link } from "react-router-dom";
import "./ui.css";

type Variant = "primary" | "accent" | "ghost" | "danger";
interface Common { variant?: Variant; small?: boolean; wide?: boolean; children: ReactNode }

const classes = ({ variant = "primary", small, wide }: Common) =>
  ["btn", variant !== "primary" && `btn--${variant}`, small && "btn--small", wide && "btn--wide"].filter(Boolean).join(" ");

export function Button({ variant, small, wide, children, ...rest }: Common & ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type="button" className={classes({ variant, small, wide, children })} {...rest}>{children}</button>;
}

/** Same look as Button, but navigates to another page. */
export function ButtonLink({ to, variant, small, wide, children }: Common & { to: string }) {
  return <Link to={to} className={classes({ variant, small, wide, children })}>{children}</Link>;
}
