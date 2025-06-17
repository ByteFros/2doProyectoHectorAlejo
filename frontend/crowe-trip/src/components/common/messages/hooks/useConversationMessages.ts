// hooks/useConversationMessages.ts
import { useState, useEffect, useCallback } from 'react';
import useAuth from '~/components/hooks/use-auth';
import { apiFetch } from '~/utils/api';

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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Al cambiar de conversación, recarga el hilo
  useEffect(() => {
    if (!token || conversationId == null) return;
    
    const fetchMessages = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await apiFetch(`/api/users/conversaciones/${conversationId}/mensajes/`, {
          method: 'GET',
        }, true);

        if (!response.ok) {
          throw new Error('Error cargando mensajes');
        }

        const data = await response.json();
        setMessages(data);
      } catch (e: any) {
        console.error('❌ Error al cargar mensajes:', e);
        setError(e.message || 'Error desconocido al cargar mensajes');
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
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
      if (archivo) form.append('archivo', archivo);

      try {
        const response = await apiFetch('/api/users/mensajes/enviar/', {
          method: 'POST',
          body: form,
        }, true);

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.error || 'Error enviando mensaje');
        }

        const msg: Message = await response.json();
        setMessages(prev => [...prev, msg]);
        return msg;
      } catch (e: any) {
        console.error('❌ Error al enviar mensaje:', e);
        throw e;
      }
    },
    [token, conversationId]
  );

  return { messages, loading, error, sendMessage };
}