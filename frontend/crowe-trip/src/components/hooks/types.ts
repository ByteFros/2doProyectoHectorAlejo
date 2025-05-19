// Trip asociado a un empleado
export interface Trip {
    id: number;
    city: string;
    country: string;
    days: string;
    reason: string;
    startDate: string; // <- Agregar esto si no estaba
}

// Gasto vinculado a un viaje (opcionalmente con recibo)
export interface Expense {
    id?: number;
    concept: string;
    amount: number;
    date?: string;
    receipt?: File;
}

// Información del clima (por si lo usás en viajes)
export interface Weather {
  description: string;
  temperature: string;
  feelsLike: string;
  icon: string;
  city: string;
}

// Empleado con viajes y gastos
export interface Empleado {
  id: number;
  nombre: string;
  dni: string;
  email: string;
  trips: Trip[];
  expenses: Expense[];
}

// ✅ Estado del justificante
export type MessageStatus = 'pendiente' | 'aprobado' | 'rechazado';

// ✅ Estructura de mensaje
export interface Message {
  id: number;
  from: string;
  content: string;
  timestamp: string;
  read: boolean;
  reply?: string;
  gastoId?: number;
  attachmentUrl?: string;
  status?: MessageStatus;
  remitente: string; // 'empleado' o 'empresa'
}

// ✅ Funciones disponibles en todos los roles
export interface MessageActions {
  messages: Message[];
  sendReply: (replyToId: number, message: string, file?: File | null) => void;
  approveJustification: (id: number) => void;
  rejectJustification: (id: number) => void;
  markAllAsRead: () => void;
  unreadCount: number;
}
