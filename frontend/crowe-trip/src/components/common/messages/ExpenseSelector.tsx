// components/ExpenseSelector.tsx
import React, { useState, useEffect } from 'react';
import styles from './messages.module.scss';
import useAuth from '~/components/hooks/use-auth';
import { apiRequest } from '@config/api';

interface Expense {
  id: number;
  concepto: string;
  monto: number;
  fecha: string;
  status: string;
}

interface ExpenseSelectorProps {
  onSelectExpense: (id: number | null) => void;
  selectedExpense: number | null;
}

const ExpenseSelector: React.FC<ExpenseSelectorProps> = ({ onSelectExpense, selectedExpense }) => {
  const { token } = useAuth();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  // Cargar gastos pendientes
  useEffect(() => {
    if (!token) return;
    
    const fetchExpenses = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await apiRequest('/gastos/pendientes/', {
          headers: {
            'Authorization': `Token ${token}`,
          },
        });
        
        if (!response.ok) {
          throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        setExpenses(data);
      } catch (err) {
        console.error('Error al cargar gastos:', err);
        setError(err instanceof Error ? err.message : 'Error desconocido');
      } finally {
        setLoading(false);
      }
    };
    
    fetchExpenses();
  }, [token]);

  const handleSelect = (expense: Expense) => {
    onSelectExpense(expense.id);
    setIsOpen(false);
  };

  const handleClear = () => {
    onSelectExpense(null);
  };

  // Formatear monto como moneda
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  // Formatear fecha
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  // Encontrar el gasto seleccionado
  const getSelectedExpense = () => {
    return expenses.find(exp => exp.id === selectedExpense);
  };

  return (
    <div className={styles.expenseSelectorContainer}>
      <div className={styles.selectorHeader}>
        <h4>Adjuntar gasto</h4>
        {selectedExpense ? (
          <div className={styles.selectedExpense}>
            <div className={styles.expenseDetails}>
              <span className={styles.expenseConcept}>{getSelectedExpense()?.concepto}</span>
              <span className={styles.expenseAmount}>{getSelectedExpense() && formatCurrency(getSelectedExpense()!.monto)}</span>
            </div>
            <button className={styles.clearButton} onClick={handleClear}>
              ×
            </button>
          </div>
        ) : (
          <button 
            className={styles.expenseSelectorButton} 
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? 'Cancelar' : 'Seleccionar gasto'}
          </button>
        )}
      </div>

      {isOpen && !selectedExpense && (
        <div className={styles.expensesDropdown}>
          {loading && <p className={styles.loadingMessage}>Cargando gastos...</p>}
          {error && <p className={styles.errorMessage}>Error: {error}</p>}
          
          {!loading && expenses.length === 0 && (
            <p className={styles.noExpensesMessage}>No tienes gastos pendientes</p>
          )}
          
          {expenses.length > 0 && (
            <ul className={styles.expensesList}>
              {expenses.map(expense => (
                <li 
                  key={expense.id} 
                  className={styles.expenseItem}
                  onClick={() => handleSelect(expense)}
                >
                  <div className={styles.expenseInfo}>
                    <span className={styles.expenseConcept}>{expense.concepto}</span>
                    <span className={styles.expenseDate}>{formatDate(expense.fecha)}</span>
                  </div>
                  <span className={styles.expenseAmount}>{formatCurrency(expense.monto)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default ExpenseSelector;