// hooks/useTripsPerMonth.ts
import { useState, useEffect } from 'react';
import { apiFetch } from '~/utils/api'; // Ajusta el path si es necesario
import useAuth from '../use-auth';

interface MonthData {
  month: string;      // '2025-03'
  totalDays: number;
}

export default function useTripsPerMonth() {
  const { token } = useAuth();
  const [data, setData] = useState<MonthData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      try {
        const response = await apiFetch('/api/users/report/trips-per-month/', {}, true);
        if (!response.ok) throw new Error('Error al obtener los viajes por mes');
        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('❌ Error al cargar datos:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { data, loading };
}
