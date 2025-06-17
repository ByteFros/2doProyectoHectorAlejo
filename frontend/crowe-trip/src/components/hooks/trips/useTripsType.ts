// hooks/useTripsType.ts
import { useState, useEffect } from 'react';
import { apiFetch } from '~/utils/api'; // Ajusta la ruta si es distinta
import useAuth from '../use-auth';

interface TripsType {
  national: number;
  international: number;
}

export default function useTripsType() {
  const { token } = useAuth();
  const [data, setData] = useState<TripsType>({ national: 0, international: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      try {
        const response = await apiFetch('/api/users/report/trips-type/', {}, true);
        if (!response.ok) throw new Error('Error al obtener el resumen de tipo de viajes');
        const result: TripsType = await response.json();
        setData(result);
      } catch (error) {
        console.error('❌ Error al cargar tipos de viajes:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { data, loading };
}
