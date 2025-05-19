// Messages.tsx
import React, { useState, useEffect } from 'react';
import styles from './messages.module.scss';
import useAuth from '../../hooks/use-auth';
import useEmployeeSearch, { Employee } from './hooks/useEmployeeSearch';
import FilePreviewModal from '~/components/common/modals/FilePreviewModal';
import useFilePreview from '~/components/hooks/files/useFilePreview';
import useConversations, { Conversacion } from './hooks/useConversations';
import useConversationMessages, { Message } from './hooks/useConversationMessages';

const Messages: React.FC = () => {
    const { role, token } = useAuth();
    const [showNotification, setShowNotification] = useState(false);
    const [notificationMessage, setNotificationMessage] = useState('');
    const [activeConversation, setActiveConversation] = useState<number | null>(null);
    const { conversations, loading: loadingConversations, createConversation } = useConversations();

    if (!role || !token) return <p className={styles.loading}>Cargando mensajes...</p>;

    const showSuccessNotification = (message: string) => {
        setNotificationMessage(message);
        setShowNotification(true);
        setTimeout(() => setShowNotification(false), 3000);
    };

    return (
        <div className={styles.panel}>
            <div className={styles.leftPanel}>

                {role !== 'EMPLEADO' && (
                    <NewMessageSection
                        showSuccessNotification={showSuccessNotification}
                        createConversation={createConversation}
                        setActiveConversation={setActiveConversation}
                    />
                )}

                <ConversationsList
                    conversations={conversations}
                    loading={loadingConversations}
                    activeConversation={activeConversation}
                    onSelectConversation={setActiveConversation}
                />
                {showNotification && (
                    <div className={styles.toastNotification}>
                        <p>{notificationMessage}</p>
                    </div>
                )}
            </div>
            <ConversationMessages
                conversationId={activeConversation}
                role={role}
                showSuccessNotification={showSuccessNotification}
            />
        </div>
    );
};

interface ConversationsListProps {
    conversations: Conversacion[];
    loading: boolean;
    activeConversation: number | null;
    onSelectConversation: (id: number) => void;
}

const ConversationsList: React.FC<ConversationsListProps> = ({
    conversations,
    loading,
    activeConversation,
    onSelectConversation
}) => {
    if (loading) return <p className={styles.loading}>Cargando conversaciones...</p>;
    if (conversations.length === 0) return <p className={styles.infoMessage}>No tienes conversaciones aún</p>;

    const formatParticipants = (participants: string[]) => {
        // Extraer nombres de los participantes (parte antes del guión)
        return participants.map(p => p.split('-')[0].trim()).join(', ');
    };

    return (
        <div className={styles.conversationsList}>
            <h3>Tus conversaciones</h3>
            <ul>
                {conversations.map(conv => (
                    <li
                        key={conv.id}
                        className={`${styles.conversationItem} ${activeConversation === conv.id ? styles.active : ''}`}
                        onClick={() => onSelectConversation(conv.id)}
                    >
                        <div className={styles.conversationHeader}>
                            <span className={styles.participants}>{formatParticipants(conv.participantes)}</span>
                            <span className={styles.date}>
                                {new Date(conv.fecha_creacion).toLocaleDateString()}
                            </span>
                        </div>
                        {conv.viaje && <span className={styles.tripBadge}>Viaje #{conv.viaje}</span>}
                    </li>
                ))}
            </ul>
        </div>
    );
};

interface NewMessageSectionProps {
    showSuccessNotification: (message: string) => void;
    createConversation: (empleadoId: number) => Promise<Conversacion>;
    setActiveConversation: (id: number) => void;
}

const NewMessageSection: React.FC<NewMessageSectionProps> = ({
    showSuccessNotification,
    createConversation,
    setActiveConversation
}) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedUser, setSelectedUser] = useState<Employee | null>(null);
    const [messageText, setMessageText] = useState('');
    const [isCreating, setIsCreating] = useState(false);
    const { suggestions, loading, error } = useEmployeeSearch(searchTerm);

    const handleSend = async () => {
        if (!messageText.trim() || !selectedUser) return;

        try {
            setIsCreating(true);
            // Primero creamos la conversación
            const newConversation = await createConversation(selectedUser.user_id);

            // Después enviaremos el primer mensaje usando el hook useConversationMessages
            // pero lo haremos después de cambiar a esa conversación
            setActiveConversation(newConversation.id);

            // Este mensaje lo enviará el ConversationMessages al detectar
            // que activeConversation ha cambiado y hay un mensaje pendiente
            localStorage.setItem('pendingMessage', messageText);

            showSuccessNotification('Conversación iniciada correctamente');
            setSelectedUser(null);
            setMessageText('');
            setSearchTerm('');
        } catch (err) {
            console.error(err);
            showSuccessNotification('Error al crear la conversación');
        } finally {
            setIsCreating(false);
        }
    };

    return (
        <div className={styles.newMessageBox}>
            <h3>Nuevo mensaje</h3>
            {!selectedUser ? (
                <>
                    <input
                        type="text"
                        placeholder="Buscar empleado o empresa..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className={styles.searchInput}
                    />
                    {loading && <p className={styles.loadingMessage}>Buscando empleados...</p>}
                    {error && <p className={styles.errorMessage}>Error: {error}</p>}
                    {suggestions.length > 0 && (
                        <ul className={styles.suggestionsList}>
                            {suggestions.map(emp => (
                                <li
                                    key={emp.id}
                                    onClick={() => setSelectedUser(emp)}
                                    className={styles.suggestionItem}
                                >
                                    {emp.nombre} {emp.apellido}
                                    <span className={styles.suggestionSubtext}>{emp.empresa}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </>
            ) : (
                <div className={styles.messageForm}>
                    <div className={styles.messageHeader}>
                        <h4>Enviar mensaje</h4>
                        <p className={styles.recipientInfo}>
                            Para: <strong>{selectedUser.nombre} {selectedUser.apellido}</strong>
                            <span className={styles.recipientCompany}> - {selectedUser.empresa}</span>
                        </p>
                    </div>
                    <textarea
                        placeholder="Escribe tu mensaje aquí..."
                        value={messageText}
                        onChange={(e) => setMessageText(e.target.value)}
                        className={styles.messageTextarea}
                    />
                    <div className={styles.messageActions}>
                        <button
                            onClick={handleSend}
                            className={styles.replyButton}
                            disabled={isCreating}
                        >
                            {isCreating ? 'Enviando...' : 'Enviar'}
                        </button>
                        <button
                            onClick={() => setSelectedUser(null)}
                            className={styles.cancelButton}
                            disabled={isCreating}
                        >
                            Cancelar
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

interface ConversationMessagesProps {
    conversationId: number | null;
    role: string;
    showSuccessNotification: (message: string) => void;
}

const ConversationMessages: React.FC<ConversationMessagesProps> = ({
    conversationId,
    role,
    showSuccessNotification
}) => {
    const { messages, loading: loadingMessages, error, sendMessage } = useConversationMessages(conversationId);
    const [newReply, setNewReply] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [selectedGasto, setSelectedGasto] = useState<number | null>(null);
    const [isSending, setIsSending] = useState(false);

    const {
        previewFile,
        isLoading,
        openPreview,
        closePreview,
        downloadFile,
    } = useFilePreview();

    // Verificar si hay un mensaje pendiente guardado en localStorage
    useEffect(() => {
        if (conversationId) {
            const pendingMessage = localStorage.getItem('pendingMessage');
            if (pendingMessage) {
                handleSendMessage(pendingMessage);
                localStorage.removeItem('pendingMessage');
            }
        }
    }, [conversationId]);

    const handleSendMessage = async (content: string = newReply) => {
        if (!content.trim() || !conversationId) return;

        try {
            setIsSending(true);
            await sendMessage(content, selectedGasto || undefined, file || undefined);
            setNewReply('');
            setFile(null);
            setSelectedGasto(null);
            showSuccessNotification('Mensaje enviado correctamente');
        } catch (err) {
            console.error(err);
            showSuccessNotification('Error al enviar el mensaje');
        } finally {
            setIsSending(false);
        }
    };

    const formatDate = (date: string) => {
        const d = new Date(date);
        return d.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getFileTypeIcon = (type: string) => {
        if (type.includes('pdf')) return '📄';
        if (type.includes('image')) return '🖼️';
        if (type.includes('text')) return '📝';
        if (type.includes('excel') || type.includes('spreadsheet')) return '📊';
        if (type.includes('word') || type.includes('document')) return '📃';
        return '📎';
    };

    if (!conversationId) {
        return (
            <div className={styles.emptyState}>
                <p>Selecciona una conversación o inicia una nueva</p>
            </div>
        );
    }

    if (loadingMessages) {
        return <p className={styles.loading}>Cargando mensajes...</p>;
    }

    if (error) {
        return <p className={styles.errorMessage}>Error: {error}</p>;
    }

    return (
        <div className={styles.messagesContainer}>
            {messages.length === 0 ? (
                <p className={styles.emptyState}>Aún no hay mensajes en esta conversación</p>
            ) : (
                <ul className={styles.messageList}>
                    {messages.map((msg) => (
                        <li
                            key={msg.id}
                            className={`${styles.messageItem} ${msg.autor.includes(role) ? styles.sent : ''}`}
                        >
                            <div className={styles.messageHeader}>
                                <strong>{msg.autor.split('-')[0].trim()}</strong>
                                <span className={styles.timestamp}>{formatDate(msg.fecha_creacion)}</span>
                            </div>
                            <p className={styles.messageContent}>{msg.contenido}</p>

                            {msg.archivo && (
                                <button
                                className={styles.viewButton}
                                onClick={() =>
                                  openPreview(
                                    msg.id,                             // 1) id
                                    'mensaje',                          // 2) categoría
                                    {                                   // 3) expenseInfo (opcional)
                                      concepto: 'Archivo adjunto',
                                      monto: msg.gasto || 0,
                                      fecha: msg.fecha_creacion,
                                    }
                                  )
                                }
                              >
                                Ver archivo adjunto {getFileTypeIcon(msg.archivo.split('.').pop() || '')}
                              </button>
                            )}

                            {msg.gasto && (
                                <div className={styles.expenseInfo}>
                                    <span>Gasto asociado: #{msg.gasto}</span>
                                </div>
                            )}
                        </li>
                    ))}
                </ul>
            )}

            <div className={styles.replyBox}>
                <textarea
                    placeholder="Escribe tu respuesta..."
                    value={newReply}
                    onChange={(e) => setNewReply(e.target.value)}
                    className={styles.replyTextarea}
                />

                <div className={styles.attachmentControls}>
                    <label className={styles.uploadLabel}>
                        Adjuntar archivo
                        <input
                            type="file"
                            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx"
                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                        />
                    </label>
                    {file && <span className={styles.fileName}>{file.name}</span>}

                    {/* Aquí podrías agregar un selector de gastos si es necesario */}
                </div>

                <button
                    className={styles.replyButton}
                    onClick={() => handleSendMessage()}
                    disabled={isSending || !newReply.trim()}
                >
                    {isSending ? 'Enviando...' : 'Enviar mensaje'}
                </button>
            </div>

            {previewFile && (
                <FilePreviewModal
                    file={previewFile || { url: '', type: '' }}
                    isLoading={isLoading}
                    onClose={closePreview}
                    onDownload={downloadFile}
                    getFileTypeIcon={getFileTypeIcon}
                    formatDate={formatDate}
                />
            )}
        </div>
    );
};

export default Messages;