// hooks/useEmployeeSearch.ts
import { useState, useEffect, useMemo } from 'react';
import { apiFetch } from '~/utils/api'; // Ajusta si el path cambia
import useAuth from '~/components/hooks/use-auth';

export interface Employee {
  id: number;
  nombre: string;
  apellido: string;
  email: string;
  empresa: string;
  user_id: number;
}

export default function useEmployeeSearch(searchTerm: string) {
  const { token } = useAuth();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 1. Cargar empleados desde backend
  useEffect(() => {
    if (!token) return;
    setLoading(true);

    const fetchData = async () => {
      try {
        const response = await apiFetch('/api/users/empleados/', {}, true);
        if (!response.ok) throw new Error('No pude cargar empleados');
        const data: Employee[] = await response.json();
        setEmployees(data);
      } catch (e) {
        console.error(e);
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  // 2. Filtro local de empleados según el término
  const suggestions = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return [];
    return employees.filter(emp => {
      const fullName = `${emp.nombre} ${emp.apellido}`.toLowerCase();
      return (
        fullName.includes(term) ||
        emp.empresa.toLowerCase().includes(term)
      );
    });
  }, [employees, searchTerm]);

  return { suggestions, loading, error };
}
