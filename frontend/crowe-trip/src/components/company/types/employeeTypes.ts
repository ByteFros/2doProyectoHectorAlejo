import { Trip, Expense, Employee } from '~/utils/triptypes';

export interface Empleado extends Employee {
  dni: string;
  email: string;
  trips: Trip[];
  expenses: Expense[];
}
