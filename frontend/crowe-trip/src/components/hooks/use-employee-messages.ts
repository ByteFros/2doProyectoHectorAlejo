// hooks/use-employee-messages.ts
import { useEffect, useState } from 'react';
import { Message, MessageActions } from './types';
import useAuth from './use-auth';

const API_BASE_URL = 'http://127.0.0.1:8000/api/users';

export function useEmployeeMessages(): MessageActions {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchMessages = async () => {
    if (!token) return;
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/mensajes/`, {
        headers: {
          Authorization: `Token ${token}`,
        },
      });

      const data = await response.json();
      const mapped = data.map((msg: any) => ({
        id: msg.id,
        from: msg.autor,
        content: msg.motivo,
        timestamp: msg.fecha_creacion,
        reply: msg.respuesta || undefined,
        attachmentUrl: `${API_BASE_URL}/gastos/${msg.gasto_id}/file/`,
        status: msg.estado,
        read: true,
      })) as Message[];

      setMessages(mapped);
    } catch (err) {
      console.error('❌ Error al cargar mensajes:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, [token]);

  const sendReply = async (replyToId: number, message: string, file?: File | null) => {
    const formData = new FormData();
    formData.append('respuesta', message);
    if (file) formData.append('archivo', file);

    try {
      await fetch(`${API_BASE_URL}/mensajes/${replyToId}/responder/`, {
        method: 'POST',
        headers: {
          Authorization: `Token ${token}`,
        },
        body: formData,
      });
      await fetchMessages();
    } catch (err) {
      console.error('❌ Error al responder mensaje:', err);
    }
  };

  const approveJustification = () => {};
  const rejectJustification = () => {};

  const markAllAsRead = () => {
    setMessages((prev) => prev.map((m) => ({ ...m, read: true })));
  };

  const unreadCount = messages.filter((m) => !m.read).length;

  return {
    messages,
    sendReply,
    approveJustification,
    rejectJustification,
    markAllAsRead,
    unreadCount,
  };
}