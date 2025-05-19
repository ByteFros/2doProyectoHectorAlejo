// hooks/useConversations.ts
import { useState, useEffect, useCallback } from 'react';
import useAuth from '~/components/hooks/use-auth';

const API_BASE = 'http://127.0.0.1:8000/api/users';

export interface Conversacion {
  id: number;
  viaje: number | null;
  participantes: string[];
  fecha_creacion: string;
}

export default function useConversations() {
  const { token } = useAuth();
  const [conversations, setConversations] = useState<Conversacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 1) Carga inicial
  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetch(`${API_BASE}/conversaciones/`, {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Error cargando conversaciones');
        return res.json();
      })
      .then((data: Conversacion[]) => setConversations(data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  // 2) Crear conversación a partir de CustomUser.id
  const createConversation = useCallback(
    async (userId: number) => {
      if (!token) throw new Error('No autorizado');
      const res = await fetch(`${API_BASE}/conversaciones/crear/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify({ empleado_id: userId }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Error creando conversación');
      }
      const newConv: Conversacion = await res.json();
      setConversations(prev => [...prev, newConv]);
      return newConv;
    },
    [token]
  );

  return { conversations, loading, error, createConversation };
}
