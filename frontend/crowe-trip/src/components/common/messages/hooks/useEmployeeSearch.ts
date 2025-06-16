// hooks/useEmployeeSearch.ts
import { useState, useEffect, useMemo } from 'react';
import useAuth from '~/components/hooks/use-auth';
import { apiRequest } from '@config/api';

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
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);

  // 1. Cargamos todos los empleados al montar
  useEffect(() => {
    if (!token) return;
    setLoading(true);
    apiRequest('/users/empleados/', {
      headers: { Authorization: `Token ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('No pude cargar empleados');
        return res.json();
      })
      .then((data: Employee[]) => {
        setEmployees(data);
      })
      .catch(e => {
        console.error(e);
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, [token]);

  // 2. Filtramos según searchTerm (nombre, apellido o empresa)
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
