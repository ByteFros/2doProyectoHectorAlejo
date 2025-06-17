// hooks/usePendingTripsDetail.ts
import { useState, useEffect } from 'react';
import { apiFetch } from '~/utils/api'; // Ajusta el path si es necesario
import useAuth from '~/components/hooks/use-auth';

export interface PendingTrip {
  id: number;
  tripDates: [string, string];
  destination: string;
  info: string;
  notes: string[];
  companyVisited: string;
  employeeName: string;
  employeeId: number;
}

export default function usePendingTripsDetail(employeeId?: number) {
  const { token } = useAuth();
  const [trips, setTrips] = useState<PendingTrip[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    setLoading(true);

    const fetchData = async () => {
      try {
        const query = employeeId ? `?empleado=${employeeId}` : '';
        const response = await apiFetch(`/api/users/viajes/pending/${query}`, {}, true);

        if (!response.ok) throw new Error('Error al cargar viajes pendientes');

        const data: { count: number; trips: PendingTrip[] } = await response.json();
        setCount(data.count);
        setTrips(data.trips);
      } catch (error) {
        console.error('❌ Error al obtener viajes pendientes:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token, employeeId]);

  return { trips, count, loading };
}
