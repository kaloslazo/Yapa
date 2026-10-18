import { useState } from 'react';
import type { ReactNode } from 'react';

interface ConfirmActionProps {
  label: ReactNode;
  question: ReactNode;
  confirmLabel?: string;
  className?: string;
  disabled?: boolean;
  onConfirm: () => void | Promise<unknown>;
}

// una acción que mueve dinero o zonas: primero pregunta, y solo con el "sí" se ejecuta
export function ConfirmAction({ label, question, confirmLabel = 'Sí', className = 'admin-row-button', disabled, onConfirm }: ConfirmActionProps) {
  const [asking, setAsking] = useState(false);
  const [busy, setBusy] = useState(false);
  const confirm = async () => {
    setBusy(true);
    try {
      await onConfirm();
    } finally {
      setBusy(false);
      setAsking(false);
    }
  };
  if (!asking) return <button className={className} type="button" disabled={disabled} onClick={() => setAsking(true)}>{label}</button>;
  return (
    <span className="confirm-action" role="group">
      <span className="confirm-question">{question}</span>
      <button className="admin-row-button" type="button" disabled={busy} onClick={() => void confirm()}>{busy ? 'Enviando…' : confirmLabel}</button>
      <button className="text-button" type="button" disabled={busy} onClick={() => setAsking(false)}>No</button>
    </span>
  );
}
