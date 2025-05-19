export interface Company {
  id: number;
  nombre: string;
}

export interface Employee {
  id: number;
  name: string;
  companyId: number;
}

export interface Trip {
  id: number;
  employeeId: number;
  destination: string;
  startDate: string; // ISO string
  endDate: string;
  expenses: Expense[];

  // Añadido para compatibilidad con Company (pero opcional)
  city?: string;
  country?: string;
  reason?: string;
}

export interface Expense {
  id: number;
  tripId: number;
  description: string;
  amount: number;
  date: string;

  status: "pending" | "validated" | "rejected" | "justify-requested";

  justificanteUrl?: string;
  receiptUrl?: string; 
}
