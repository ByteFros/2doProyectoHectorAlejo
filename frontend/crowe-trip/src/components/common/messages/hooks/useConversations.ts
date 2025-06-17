// hooks/useConversations.ts
import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '~/utils/api'; // Asegúrate de que el path sea correcto
import useAuth from '~/components/hooks/use-auth';

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

    const fetchData = async () => {
      try {
        const response = await apiFetch('/api/users/conversaciones/', {}, true);
        if (!response.ok) throw new Error('Error cargando conversaciones');
        const data: Conversacion[] = await response.json();
        setConversations(data);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  // 2) Crear conversación a partir de CustomUser.id
  const createConversation = useCallback(
    async (userId: number) => {
      if (!token) throw new Error('No autorizado');

      const response = await apiFetch(
        '/api/users/conversaciones/crear/',
        {
          method: 'POST',
          body: JSON.stringify({ empleado_id: userId }),
        },
        true
      );

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Error creando conversación');
      }

      const newConv: Conversacion = await response.json();
      setConversations(prev => [...prev, newConv]);
      return newConv;
    },
    [token]
  );

  return { conversations, loading, error, createConversation };
}
