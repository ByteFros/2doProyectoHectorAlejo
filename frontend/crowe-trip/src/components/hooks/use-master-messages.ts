// hooks/use-master-messages.ts
import { useEffect, useState } from 'react';
import { Message, MessageActions } from './types';
import useAuth from './use-auth';
import { buildApiUrl } from '../../config/api';

export function useMasterMessages(): MessageActions {
    const { token } = useAuth();
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchMessages = async () => {
        if (!token) return;
        setLoading(true);

        try {
            const response = await fetch(buildApiUrl('/users/mensajes/'), {
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
                attachmentUrl: buildApiUrl(`/users/gastos/${msg.gasto_id}/file/`),
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

    const approveJustification = async (id: number) => {
        try {
            await fetch(buildApiUrl(`/users/mensajes/${id}/cambiar-estado/`), {
                method: 'POST',
                headers: {
                    Authorization: `Token ${token}`,
                },
                body: JSON.stringify({ estado: 'aprobado' }),
            });
            setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, status: 'aprobado' } : m)));
        } catch (err) {
            console.error('❌ Error al aprobar justificante:', err);
        }
    };

    const rejectJustification = async (id: number) => {
        try {
            await fetch(buildApiUrl(`/users/mensajes/${id}/cambiar-estado/`), {
                method: 'POST',
                headers: {
                    Authorization: `Token ${token}`,
                },
                body: JSON.stringify({ estado: 'rechazado' }),
            });
            setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, status: 'rechazado' } : m)));
        } catch (err) {
            console.error('❌ Error al rechazar justificante:', err);
        }
    };

    const sendReply = async (replyToId: number, message: string, file?: File | null) => {
        const formData = new FormData();
        formData.append('respuesta', message);
        if (file) formData.append('archivo', file);

        try {
            await fetch(buildApiUrl(`/users/mensajes/${replyToId}/responder/`), {
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