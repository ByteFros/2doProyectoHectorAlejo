// hooks/usePendingEmployeesByCompany.ts
import { useState, useEffect } from 'react';
import { apiFetch } from '~/utils/api'; // Ajusta si es necesario
import useAuth from '~/components/hooks/use-auth';

export interface Employee {
  id: number;
  nombre: string;
  apellido: string;
  dni: string;
  email: string;
  empresa: string;
}

export default function usePendingEmployeesByCompany(companyId?: number) {
  const { token } = useAuth();
  const [data, setData] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token || !companyId) return;

    const fetchData = async () => {
      try {
        const response = await apiFetch(
          `/api/users/empresas/${companyId}/empleados/pending/`,
          {},
          true
        );

        if (!response.ok) throw new Error('Error cargando empleados pendientes');

        const emps: Employee[] = await response.json();
        setData(emps);
      } catch (error) {
        console.error('❌ Error al obtener empleados pendientes:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token, companyId]);

  return { data, loading };
}
