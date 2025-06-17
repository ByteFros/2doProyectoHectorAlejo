// hooks/usePendingCompanies.ts
import { useState, useEffect } from 'react';
import { apiFetch } from '~/utils/api'; // Asegúrate de que esta ruta sea válida
import useAuth from '~/components/hooks/use-auth';

interface Company {
  id: number;
  nombre_empresa: string;
}

export default function usePendingCompanies() {
  const { token } = useAuth();
  const [data, setData] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      try {
        const response = await apiFetch('/api/users/report/companies/pending/', {}, true);
        if (!response.ok) throw new Error('Error al obtener las empresas pendientes');
        const result: Company[] = await response.json();
        setData(result);
      } catch (error) {
        console.error('❌ Error al cargar empresas pendientes:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { data, loading };
}
