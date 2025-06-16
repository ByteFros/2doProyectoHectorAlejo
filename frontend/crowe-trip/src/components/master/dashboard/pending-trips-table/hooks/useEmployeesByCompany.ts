// hooks/usePendingEmployeesByCompany.ts
import { useState, useEffect } from 'react';
import useAuth from '~/components/hooks/use-auth';
import { apiRequest } from '@config/api';

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

    apiRequest(`/users/empresas/${companyId}/empleados/pending/`, {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Error cargando empleados pendientes');
        return res.json();
      })
      .then((emps: Employee[]) => setData(emps))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token, companyId]);

  return { data, loading };
}
