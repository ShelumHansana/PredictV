import type { InputHTMLAttributes } from "react";
import "./ui.css";

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange"> { label: string; hint?: string; onValue: (value: string) => void }

export function Field({ label, hint, id, onValue, ...rest }: Props) {
  return (
    <label className="field" htmlFor={id}>
      <span className="field__label">{label}</span>
      <input id={id} className="field__input" onChange={e => onValue(e.target.value)} {...rest} />
      {hint && <span className="field__hint" style={{ display: "block" }}>{hint}</span>}
    </label>
  );
}
