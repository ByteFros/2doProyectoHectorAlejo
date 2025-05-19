import { useState } from 'react';
import styles from './request-proof-modal.module.scss';

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (motivo: string) => void;
}

export default function RequestProofModal({ open, onClose, onSubmit }: Props) {
  const [motivo, setMotivo] = useState('');
  const [error, setError] = useState('');

  if (!open) return null;

  const handleSubmit = () => {
    if (!motivo.trim()) {
      setError('Debes escribir una explicación');
      return;
    }

    setError('');
    onSubmit(motivo);
    setMotivo('');
    onClose();
  };

  return (
    <div className={styles.modalBackdrop} onClick={onClose}>
      <div className={styles.modalBox} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>Solicitar justificante</h2>
        <textarea
          className={styles.textarea}
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          placeholder="Explica por qué se requiere el justificante..."
        />
        {error && <p className={styles.error}>{error}</p>}
        <div className={styles.buttons}>
          <button onClick={handleSubmit} className={styles.submit}>Enviar</button>
          <button onClick={onClose} className={styles.cancel}>Cancelar</button>
        </div>
      </div>
    </div>
  );
}
