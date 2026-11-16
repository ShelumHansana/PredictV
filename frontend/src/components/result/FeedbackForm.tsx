import { useState, type FormEvent } from "react";
import { api } from "../../api/client";
import type { Diagnosis, Meta } from "../../api/types";
import { useI18n } from "../../i18n/I18nProvider";
import { Button } from "../ui/Button";
import { Notice } from "../ui/Notice";
import { Panel } from "../ui/Panel";
import "./result.css";

interface Props { diagnosis: Diagnosis; meta: Meta; onSaved: (d: Diagnosis) => void }

/** Lets the rider record what the mechanic actually found. These answers train the learned model. */
export function FeedbackForm({ diagnosis, meta, onSaved }: Props) {
  const { t, lang } = useI18n();
  const saved = diagnosis.feedback;
  const [editing, setEditing] = useState(!saved);
  const [fault, setFault] = useState(saved?.confirmed_fault ?? "");
  const [note, setNote] = useState(saved?.note ?? "");
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  const name = (id: string) => id === "other" ? t("fb_other") : id === "none" ? t("fb_none") : (meta.faults[id]?.[lang] ?? id);
  // the faults this check suggested first, then every other fault
  const suggested = diagnosis.result.faults.map(f => f.id);
  const rest = Object.keys(meta.faults).filter(id => !suggested.includes(id));

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!fault) return;
    setBusy(true);
    setFailed(false);
    try {
      onSaved(await api.saveFeedback(diagnosis.id, fault, note.trim()));
      setEditing(false);
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  if (saved && !editing) {
    return (
      <Panel title={t("fb_h")}>
        <div className="feedback__saved">
          <span><b>{name(saved.confirmed_fault)}</b>{saved.note ? ` — ${saved.note}` : ""}</span>
          <span className="muted small">{t("fb_saved")}</span>
          <Button variant="ghost" small onClick={() => setEditing(true)}>{t("fb_change")}</Button>
        </div>
      </Panel>
    );
  }

  return (
    <Panel title={t("fb_h")}>
      <form className="feedback stack no-print" onSubmit={submit}>
        <p className="muted small" style={{ margin: 0 }}>{t("fb_intro")}</p>
        <label className="field" htmlFor="fb-fault">
          <span className="visually-hidden">{t("fb_h")}</span>
          <select id="fb-fault" className="field__input" value={fault} onChange={e => setFault(e.target.value)} required>
            <option value="" disabled>—</option>
            {suggested.map(id => <option key={id} value={id}>{name(id)}</option>)}
            {rest.map(id => <option key={id} value={id}>{name(id)}</option>)}
            <option value="other">{t("fb_other")}</option>
            <option value="none">{t("fb_none")}</option>
          </select>
        </label>
        <label className="field" htmlFor="fb-note">
          <span className="field__label">{t("fb_note")}</span>
          <textarea id="fb-note" className="field__input" maxLength={500} value={note} onChange={e => setNote(e.target.value)} />
        </label>
        {failed && <Notice error>{t("server")}</Notice>}
        <div><Button type="submit" disabled={busy || !fault}>{t("fb_save")}</Button></div>
      </form>
    </Panel>
  );
}
