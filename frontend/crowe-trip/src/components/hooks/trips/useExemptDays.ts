// hooks/useExemptDays.ts
import { useState, useEffect } from 'react';
import { apiFetch } from '~/utils/api'; // Asegúrate de ajustar la ruta si es necesario
import useAuth from '../use-auth';

interface ExemptDays {
  exempt: number;
  nonExempt: number;
}

export default function useExemptDays() {
  const { token } = useAuth();
  const [data, setData] = useState<ExemptDays>({ exempt: 0, nonExempt: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        const response = await apiFetch('/api/users/report/exempt-days/', {}, true);
        if (!response.ok) throw new Error('Error al obtener los días exentos');
        const result: ExemptDays = await response.json();
        setData(result);
      } catch (error) {
        console.error('❌ Error al cargar días exentos:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { data, loading };
}
