// hooks/useConversationMessages.ts
import { useState, useEffect, useCallback } from 'react';
import useAuth from '~/components/hooks/use-auth';
import { buildApiUrl } from '@config/api';

export interface Message {
  id: number;
  conversacion: number;
  autor: string;       // "master - MASTER" o "Empleado - EMPLEADO"
  contenido: string;
  archivo: string | null;
  gasto: number | null;
  fecha_creacion: string;
  // puedes mapear campos adicionales si tu serializer los expone
}

export default function useConversationMessages(conversationId: number | null) {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  // 1. Al cambiar de conversación, recarga el hilo
  useEffect(() => {
    if (!token || conversationId == null) return;
    setLoading(true);
    fetch(buildApiUrl(`/conversaciones/${conversationId}/mensajes/`), {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Error cargando mensajes');
        return res.json();
      })
      .then((data: Message[]) => setMessages(data))
      .catch(e => {
        console.error(e);
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, [token, conversationId]);

  // 2. Enviar nuevo mensaje (texto + opcional gasto + opcional archivo)
  const sendMessage = useCallback(
    async (
      contenido: string,
      gastoId?: number,
      archivo?: File
    ) => {
      if (!token || conversationId == null) {
        throw new Error('Faltan datos para enviar mensaje');
      }
      const form = new FormData();
      form.append('conversacion_id', String(conversationId));
      form.append('contenido', contenido);
      if (gastoId != null) form.append('gasto_id', String(gastoId));
      if (archivo)    form.append('archivo', archivo);

      const res = await fetch(buildApiUrl('/mensajes/enviar/'), {
        method: 'POST',
        headers: {
          Authorization: `Token ${token}`,
        },
        body: form,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Error enviando mensaje');
      }
      const msg: Message = await res.json();
      setMessages(prev => [...prev, msg]);
      return msg;
    },
    [token, conversationId]
  );

  return { messages, loading, error, sendMessage };
}
